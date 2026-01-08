# backend/routes/kpi_red.py
from __future__ import annotations

from fastapi import APIRouter
import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "races.db")

router = APIRouter(prefix="/api/kpi", tags=["kpi"])


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/red")
def red_history(limit: int = 100):
    conn = _conn()
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT ts, red_score, level, paused
        FROM red_history
        ORDER BY id DESC
        LIMIT ?
    """, (limit,)).fetchall()

    conn.close()

    return {
        "items": [
            {
                "ts": r["ts"],
                "red_score": float(r["red_score"]),
                "level": r["level"],
                "paused": bool(r["paused"]),
            }
            for r in reversed(rows)
        ]
    }
