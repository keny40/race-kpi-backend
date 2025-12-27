import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.getenv("DB_PATH", "races.db")
RED_THRESHOLD = int(os.getenv("RED_THRESHOLD", "3"))  # N회

def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def record_status(status: str):
    conn = _conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS system_status_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        status TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
        INSERT INTO system_status_log (status, created_at)
        VALUES (?, ?)
    """, (status, datetime.utcnow().isoformat()))

    conn.commit()
    conn.close()


def is_red_consecutive():
    conn = _conn()
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT status
        FROM system_status_log
        ORDER BY created_at DESC
        LIMIT ?
    """, (RED_THRESHOLD,)).fetchall()

    conn.close()

    if len(rows) < RED_THRESHOLD:
        return False

    return all(r["status"] == "RED" for r in rows)
