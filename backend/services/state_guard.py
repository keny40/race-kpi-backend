# backend/services/state_guard.py

import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "races.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_system_state():
    """
    RED / YELLOW / GREEN 판단
    """
    conn = get_conn()
    cur = conn.cursor()

    row = cur.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN result = 'HIT' THEN 1 ELSE 0 END) AS hit,
            SUM(CASE WHEN result = 'MISS' THEN 1 ELSE 0 END) AS miss
        FROM v_race_match
        WHERE result IN ('HIT', 'MISS')
    """).fetchone()

    conn.close()

    total = row["total"] or 0
    hit = row["hit"] or 0
    miss = row["miss"] or 0

    accuracy = hit / total if total > 0 else 0

    if total < 5:
        return "RED"  # 데이터 부족

    if accuracy < 0.4:
        return "RED"
    if accuracy < 0.55:
        return "YELLOW"
    return "GREEN"
