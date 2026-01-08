# backend/services/collect_logs.py
import sqlite3
from datetime import datetime

DB_PATH = "backend/races.db"

def push_collect_log(log: dict):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO collect_logs (
            time, filename, source, status,
            inserted, skipped, pre_race, error
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        log.get("filename"),
        log.get("source"),
        log.get("status"),
        log.get("inserted"),
        log.get("skipped"),
        log.get("pre_race"),
        log.get("error"),
    ))

    conn.commit()
    conn.close()
