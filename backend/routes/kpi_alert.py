# backend/routes/kpi_alert.py

from fastapi import APIRouter
import sqlite3
import os
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "races.db")

router = APIRouter(prefix="/api/kpi/alert", tags=["kpi-alert"])


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_current_status(cur):
    row = cur.execute("""
        SELECT status
        FROM kpi_status_history
        ORDER BY created_at DESC
        LIMIT 1
    """).fetchone()
    return row["status"] if row else None


def calc_current_status(cur):
    row = cur.execute("""
        SELECT
            SUM(CASE WHEN result = 'HIT' THEN 1 ELSE 0 END) AS hit,
            SUM(CASE WHEN result = 'MISS' THEN 1 ELSE 0 END) AS miss
        FROM v_race_match
    """).fetchone()

    hit = row["hit"] or 0
    miss = row["miss"] or 0
    total = hit + miss

    if total == 0:
        return "RED", 0

    acc = hit / total

    if acc >= 0.6:
        return "GREEN", acc
    elif acc >= 0.5:
        return "YELLOW", acc
    else:
        return "RED", acc


@router.post("/check")
def check_and_record():
    conn = _conn()
    cur = conn.cursor()

    # 테이블 보장
    cur.execute("""
        CREATE TABLE IF NOT EXISTS kpi_status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL,
            accuracy REAL,
            created_at TEXT NOT NULL
        )
    """)

    prev_status = get_current_status(cur)
    curr_status, acc = calc_current_status(cur)

    status_changed = prev_status != curr_status

    cur.execute("""
        INSERT INTO kpi_status_history (status, accuracy, created_at)
        VALUES (?, ?, ?)
    """, (
        curr_status,
        acc,
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()

    return {
        "previous": prev_status,
        "current": curr_status,
        "accuracy": round(acc, 3),
        "changed": status_changed
    }
