# backend/services/log_store.py
import os
import json
import sqlite3
from typing import Any, Dict, List, Optional

DB_PATH = os.getenv("DB_PATH", "races.db")


def _conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_tables():
    conn = _conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ops_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
        action TEXT NOT NULL,
        level TEXT NOT NULL DEFAULT 'INFO',
        detail_json TEXT NOT NULL DEFAULT '{}'
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ops_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
        score REAL NOT NULL,
        is_red INTEGER NOT NULL,
        streak INTEGER NOT NULL,
        paused INTEGER NOT NULL,
        reasons_json TEXT NOT NULL DEFAULT '{}'
    )
    """)

    conn.commit()
    conn.close()


def insert_log(action: str, detail: Optional[Dict[str, Any]] = None, level: str = "INFO"):
    ensure_tables()
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO ops_logs(action, level, detail_json) VALUES(?,?,?)",
        (action, level, json.dumps(detail or {}, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


def insert_run_snapshot(score: float, is_red: bool, streak: int, paused: bool, reasons: Dict[str, Any]):
    ensure_tables()
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO ops_runs(score, is_red, streak, paused, reasons_json) VALUES(?,?,?,?,?)",
        (float(score), 1 if is_red else 0, int(streak), 1 if paused else 0, json.dumps(reasons or {}, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


def query_logs(
    actions: Optional[List[str]] = None,
    levels: Optional[List[str]] = None,
    limit: int = 200,
    offset: int = 0,
):
    ensure_tables()
    conn = _conn()
    cur = conn.cursor()

    where = []
    params: List[Any] = []

    if actions:
        where.append("action IN ({})".format(",".join(["?"] * len(actions))))
        params.extend(actions)

    if levels:
        where.append("level IN ({})".format(",".join(["?"] * len(levels))))
        params.extend(levels)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    sql = f"""
        SELECT id, ts, action, level, detail_json
        FROM ops_logs
        {where_sql}
        ORDER BY id DESC
        LIMIT ? OFFSET ?
    """
    params.extend([int(limit), int(offset)])

    rows = cur.execute(sql, params).fetchall()
    conn.close()

    out = []
    for r in rows:
        out.append({
            "id": r["id"],
            "ts": r["ts"],
            "action": r["action"],
            "level": r["level"],
            "detail": json.loads(r["detail_json"] or "{}"),
        })
    return out


def query_logs_csv(actions: Optional[List[str]] = None, levels: Optional[List[str]] = None, limit: int = 5000):
    # CSV는 최신 limit건만
    ensure_tables()
    conn = _conn()
    cur = conn.cursor()

    where = []
    params: List[Any] = []

    if actions:
        where.append("action IN ({})".format(",".join(["?"] * len(actions))))
        params.extend(actions)

    if levels:
        where.append("level IN ({})".format(",".join(["?"] * len(levels))))
        params.extend(levels)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    sql = f"""
        SELECT id, ts, action, level, detail_json
        FROM ops_logs
        {where_sql}
        ORDER BY id DESC
        LIMIT ?
    """
    params.append(int(limit))
    rows = cur.execute(sql, params).fetchall()
    conn.close()
    return rows


def query_red_history(bucket: str = "hour", days: int = 3):
    """
    bucket: hour | day
    days: 최근 N일
    """
    ensure_tables()
    conn = _conn()
    cur = conn.cursor()

    if bucket == "day":
        grp = "substr(ts, 1, 10)"  # YYYY-MM-DD
        label = "day"
    else:
        grp = "substr(ts, 1, 13)"  # YYYY-MM-DDTHH
        label = "hour"

    rows = cur.execute(f"""
        SELECT {grp} AS bucket, COUNT(*) AS c
        FROM ops_runs
        WHERE is_red = 1
          AND ts >= datetime('now', ?)
        GROUP BY {grp}
        ORDER BY bucket ASC
    """, (f"-{int(days)} day",)).fetchall()

    conn.close()

    labels = [r["bucket"] for r in rows]
    counts = [r["c"] for r in rows]
    return {"bucket": label, "labels": labels, "counts": counts}
