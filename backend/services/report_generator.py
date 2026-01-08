from __future__ import annotations
import sqlite3, os
from datetime import datetime, timedelta

DB_PATH = os.getenv("DB_PATH", "races.db")

def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def generate_report(days: int = 1) -> dict:
    since = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

    conn = _conn()
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT
          json_extract(meta,'$.confidence') AS confidence,
          json_extract(meta,'$.result') AS result
        FROM admin_logs
        WHERE action='ACTUAL'
          AND ts >= ?
    """, (since,)).fetchall()
    conn.close()

    total = hit = miss = hi_conf_hit = hi_conf_miss = 0

    for r in rows:
        c = r["confidence"]
        if c is None:
            continue
        c = float(c)
        if r["result"] == "HIT":
            hit += 1
            if c >= 0.65: hi_conf_hit += 1
        elif r["result"] == "MISS":
            miss += 1
            if c >= 0.65: hi_conf_miss += 1
        total += 1

    def rate(h, m):
        return (h / (h+m)) if (h+m) else None

    return {
        "period_days": days,
        "total_samples": total,
        "hit": hit,
        "miss": miss,
        "hit_rate": rate(hit, miss),
        "hi_conf_hit": hi_conf_hit,
        "hi_conf_miss": hi_conf_miss,
        "hi_conf_hit_rate": rate(hi_conf_hit, hi_conf_miss),
    }
