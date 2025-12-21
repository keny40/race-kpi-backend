# backend/storage.py
import sqlite3
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any, Optional

DB_PATH = "races.db"

KPI_RULES = {
    "roi_danger": -0.10,
    "hit_rate_min": 0.40,
    "pass_rate_max": 0.45,
}

def _connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db(default_strategies: Optional[List[str]] = None):
    """
    기존 테이블(predictions 등)은 이미 있다고 가정
    추가로 alert_history, strategy_config를 생성
    """
    if default_strategies is None:
        default_strategies = ["baseline", "streak_guard", "threshold_055", "threshold_060", "aggressive"]

    con = _connect()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS alert_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        days INTEGER NOT NULL,
        roi REAL NOT NULL,
        hit_rate REAL NOT NULL,
        pass_rate REAL NOT NULL,
        warnings_text TEXT NOT NULL,
        sent_slack INTEGER NOT NULL DEFAULT 0,
        sent_mail INTEGER NOT NULL DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS strategy_config (
        strategy TEXT PRIMARY KEY,
        is_enabled INTEGER NOT NULL DEFAULT 1,
        updated_at TEXT NOT NULL
    )
    """)

    # seed config rows
    now = datetime.utcnow().isoformat()
    for s in default_strategies:
        cur.execute("""
        INSERT OR IGNORE INTO strategy_config(strategy, is_enabled, updated_at)
        VALUES (?, 1, ?)
        """, (s, now))

    con.commit()
    con.close()


def get_strategy_config() -> List[Dict[str, Any]]:
    con = _connect()
    cur = con.cursor()
    rows = cur.execute("""
        SELECT strategy, is_enabled, updated_at
        FROM strategy_config
        ORDER BY strategy
    """).fetchall()
    con.close()
    return [{"strategy": r["strategy"], "is_enabled": bool(r["is_enabled"]), "updated_at": r["updated_at"]} for r in rows]


def set_strategy_enabled(strategy: str, is_enabled: bool) -> None:
    con = _connect()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO strategy_config(strategy, is_enabled, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(strategy) DO UPDATE SET
            is_enabled=excluded.is_enabled,
            updated_at=excluded.updated_at
    """, (strategy, 1 if is_enabled else 0, datetime.utcnow().isoformat()))
    con.commit()
    con.close()


def _enabled_strategy_set() -> set:
    con = _connect()
    cur = con.cursor()
    rows = cur.execute("SELECT strategy FROM strategy_config WHERE is_enabled=1").fetchall()
    con.close()
    return set([r[0] for r in rows])


def fetch_kpi(days: int) -> Dict:
    """
    predictions 테이블의 decision 값(HIT/MISS/PASS)을 기준으로 KPI 계산
    """
    con = _connect()
    cur = con.cursor()

    rows = cur.execute("""
        SELECT decision
        FROM predictions
        WHERE created_at >= date('now', ?)
    """, (f"-{days} day",)).fetchall()

    con.close()

    hits = miss = passed = 0
    for (d,) in rows:
        if d == "PASS":
            passed += 1
        elif d == "HIT":
            hits += 1
        else:
            miss += 1

    bets = hits + miss
    roi = (hits - miss) / max(1, bets)
    hit_rate = hits / max(1, bets)
    pass_rate = passed / max(1, (bets + passed))

    return {
        "roi": round(roi, 3),
        "hit_rate": round(hit_rate, 3),
        "pass_rate": round(pass_rate, 3),
        "bets": bets,
        "hits": hits,
        "miss": miss,
        "pass": passed,
    }


def kpi_warning(kpi: Dict) -> List[str]:
    w = []
    if kpi["roi"] < KPI_RULES["roi_danger"]:
        w.append("ROI 위험")
    if kpi["hit_rate"] < KPI_RULES["hit_rate_min"]:
        w.append("적중률 저조")
    if kpi["pass_rate"] > KPI_RULES["pass_rate_max"]:
        w.append("PASS 과다")
    return w


def log_alert_history(days: int, kpi: Dict, warnings: List[str], sent_slack: bool, sent_mail: bool) -> int:
    con = _connect()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO alert_history(created_at, days, roi, hit_rate, pass_rate, warnings_text, sent_slack, sent_mail)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.utcnow().isoformat(),
        int(days),
        float(kpi["roi"]),
        float(kpi["hit_rate"]),
        float(kpi["pass_rate"]),
        "\n".join(warnings) if warnings else "",
        1 if sent_slack else 0,
        1 if sent_mail else 0
    ))
    con.commit()
    new_id = cur.lastrowid
    con.close()
    return int(new_id)


def fetch_alert_history(limit: int = 100) -> List[Dict[str, Any]]:
    con = _connect()
    cur = con.cursor()
    rows = cur.execute("""
        SELECT id, created_at, days, roi, hit_rate, pass_rate, warnings_text, sent_slack, sent_mail
        FROM alert_history
        ORDER BY id DESC
        LIMIT ?
    """, (int(limit),)).fetchall()
    con.close()

    out = []
    for r in rows:
        out.append({
            "id": r["id"],
            "created_at": r["created_at"],
            "days": r["days"],
            "roi": r["roi"],
            "hit_rate": r["hit_rate"],
            "pass_rate": r["pass_rate"],
            "warnings": r["warnings_text"].split("\n") if r["warnings_text"] else [],
            "sent_slack": bool(r["sent_slack"]),
            "sent_mail": bool(r["sent_mail"]),
        })
    return out


def fetch_strategy_kpi(days: int, only_enabled: bool = True) -> Dict[str, Dict]:
    enabled = _enabled_strategy_set() if only_enabled else None

    con = _connect()
    cur = con.cursor()

    rows = cur.execute("""
        SELECT strategy, decision
        FROM predictions
        WHERE created_at >= date('now', ?)
    """, (f"-{days} day",)).fetchall()

    con.close()

    acc = defaultdict(lambda: {"hits": 0, "miss": 0, "pass": 0})
    for s, d in rows:
        if enabled is not None and s not in enabled:
            continue
        if d == "PASS":
            acc[s]["pass"] += 1
        elif d == "HIT":
            acc[s]["hits"] += 1
        else:
            acc[s]["miss"] += 1

    out = {}
    for s, v in acc.items():
        bets = v["hits"] + v["miss"]
        out[s] = {
            "roi": round((v["hits"] - v["miss"]) / max(1, bets), 3),
            "hit_rate": round(v["hits"] / max(1, bets), 3),
            "pass_rate": round(v["pass"] / max(1, (bets + v["pass"])), 3),
            "bets": bets,
            "hits": v["hits"],
            "miss": v["miss"],
            "pass": v["pass"],
        }
    return out


def fetch_strategy_trend(period: str = "month", only_enabled: bool = True) -> Dict[str, List[Dict[str, Any]]]:
    enabled = _enabled_strategy_set() if only_enabled else None

    con = _connect()
    cur = con.cursor()

    if period == "month":
        key = "strftime('%Y-%m', created_at)"
    else:
        key = "strftime('%Y', created_at)||'-Q'||((cast(strftime('%m',created_at) as int)-1)/3+1)"

    rows = cur.execute(f"""
        SELECT strategy, {key} AS p,
               SUM(CASE WHEN decision='HIT' THEN 1 ELSE 0 END) AS hits,
               SUM(CASE WHEN decision='MISS' THEN 1 ELSE 0 END) AS miss,
               SUM(CASE WHEN decision='PASS' THEN 1 ELSE 0 END) AS pass
        FROM predictions
        GROUP BY strategy, p
        ORDER BY p
    """).fetchall()

    con.close()

    out = defaultdict(list)
    for s, p, h, m, pa in rows:
        if enabled is not None and s not in enabled:
            continue
        bets = int(h) + int(m)
        out[s].append({
            "period": p,
            "roi": round((int(h) - int(m)) / max(1, bets), 3),
            "hit_rate": round(int(h) / max(1, bets), 3),
            "pass_rate": round(int(pa) / max(1, (bets + int(pa))), 3),
            "bets": bets,
            "hits": int(h),
            "miss": int(m),
            "pass": int(pa),
        })
    return out
