import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_DB_PATH = HERE / "races.db"
SCHEMA_PATH = HERE / "schema.sql"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_db_path() -> str:
    return os.environ.get("DB_PATH", str(DEFAULT_DB_PATH))


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(
        get_db_path(),
        check_same_thread=False,
        timeout=30,
    )
    con.row_factory = sqlite3.Row
    return con


def bootstrap_db() -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    con = connect()
    try:
        con.executescript(schema)
        con.commit()
    finally:
        con.close()


def _latest_base_sql() -> str:
    """
    race_id별 predictions 중 created_at 최신 1건만 KPI에 반영
    """
    return """
    WITH latest AS (
      SELECT p.*
      FROM predictions p
      JOIN (
        SELECT race_id, MAX(created_at) AS max_created_at
        FROM predictions
        GROUP BY race_id
      ) t
      ON p.race_id = t.race_id AND p.created_at = t.max_created_at
    )
    """


def compute_kpi_overall(con: sqlite3.Connection) -> dict:
    base = _latest_base_sql()

    total = con.execute(base + "SELECT COUNT(*) c FROM latest").fetchone()["c"]
    pass_cnt = con.execute(base + "SELECT COUNT(*) c FROM latest WHERE decision='PASS'").fetchone()["c"]

    row = con.execute(
        base + """
        SELECT
          SUM(CASE WHEN l.decision!='PASS' AND a.actual_label=l.decision THEN 1 ELSE 0 END) hit,
          SUM(CASE WHEN l.decision!='PASS' AND a.actual_label IS NOT NULL AND a.actual_label!=l.decision THEN 1 ELSE 0 END) miss
        FROM latest l
        LEFT JOIN actual_results a ON a.race_id=l.race_id
        """
    ).fetchone()

    hit = int(row["hit"] or 0)
    miss = int(row["miss"] or 0)
    denom = hit + miss

    hit_rate = (hit / denom) if denom > 0 else 0.0
    pass_rate = (pass_cnt / total) if total > 0 else 0.0

    return {
        "asof_at": _utc_now_iso(),
        "total": int(total),
        "hit": hit,
        "miss": miss,
        "pass": int(pass_cnt),
        "hit_rate": float(hit_rate),
        "pass_rate": float(pass_rate),
    }


def compute_kpi_by_model(con: sqlite3.Connection) -> list[dict]:
    base = _latest_base_sql()

    rows = con.execute(
        base + """
        SELECT
          l.model_name AS model_name,
          COUNT(*) AS total,
          SUM(CASE WHEN l.decision='PASS' THEN 1 ELSE 0 END) AS pass_cnt,
          SUM(CASE WHEN l.decision!='PASS' AND a.actual_label=l.decision THEN 1 ELSE 0 END) AS hit,
          SUM(CASE WHEN l.decision!='PASS' AND a.actual_label IS NOT NULL AND a.actual_label!=l.decision THEN 1 ELSE 0 END) AS miss
        FROM latest l
        LEFT JOIN actual_results a ON a.race_id=l.race_id
        GROUP BY l.model_name
        ORDER BY l.model_name
        """
    ).fetchall()

    out: list[dict] = []
    for r in rows:
        hit = int(r["hit"] or 0)
        miss = int(r["miss"] or 0)
        total = int(r["total"] or 0)
        pass_cnt = int(r["pass_cnt"] or 0)
        denom = hit + miss

        out.append({
            "model_name": r["model_name"],
            "total": total,
            "hit": hit,
            "miss": miss,
            "pass": pass_cnt,
            "hit_rate": float(hit / denom) if denom > 0 else 0.0,
            "pass_rate": float(pass_cnt / total) if total > 0 else 0.0,
        })
    return out


def compute_kpi_trend_daily(con: sqlite3.Connection, limit_days: int = 14) -> list[dict]:
    """
    일 단위 KPI 트렌드 (race_id 최신 1건 기준)
    - day = created_at(YYYY-MM-DD)
    """
    base = _latest_base_sql()

    rows = con.execute(
        base + """
        SELECT
          substr(l.created_at, 1, 10) AS day,
          COUNT(*) AS total,
          SUM(CASE WHEN l.decision='PASS' THEN 1 ELSE 0 END) AS pass_cnt,
          SUM(CASE WHEN l.decision!='PASS' AND a.actual_label=l.decision THEN 1 ELSE 0 END) AS hit,
          SUM(CASE WHEN l.decision!='PASS' AND a.actual_label IS NOT NULL AND a.actual_label!=l.decision THEN 1 ELSE 0 END) AS miss
        FROM latest l
        LEFT JOIN actual_results a ON a.race_id=l.race_id
        GROUP BY day
        ORDER BY day DESC
        LIMIT ?
        """,
        (int(limit_days),),
    ).fetchall()

    out: list[dict] = []
    for r in rows:
        hit = int(r["hit"] or 0)
        miss = int(r["miss"] or 0)
        total = int(r["total"] or 0)
        pass_cnt = int(r["pass_cnt"] or 0)
        denom = hit + miss

        out.append({
            "day": r["day"],
            "total": total,
            "hit": hit,
            "miss": miss,
            "pass": pass_cnt,
            "hit_rate": float(hit / denom) if denom > 0 else 0.0,
        })

    # 오래된 날짜 → 최신 날짜 순으로 반환
    return list(reversed(out))
