from fastapi import APIRouter
import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "races.db")

router = APIRouter(prefix="/api/kpi/status", tags=["kpi-status"])


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def judge_status(total: int, hit: int, miss: int):
    decided = hit + miss
    accuracy = hit / decided if decided > 0 else 0

    if decided >= 10 and accuracy >= 0.60:
        return "GREEN", accuracy
    if decided >= 5 and accuracy >= 0.50:
        return "YELLOW", accuracy
    return "RED", accuracy


@router.get("")
def get_kpi_status():
    conn = _conn()
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT result
        FROM v_race_match
        WHERE result IN ('HIT', 'MISS')
    """).fetchall()

    hit = sum(1 for r in rows if r["result"] == "HIT")
    miss = sum(1 for r in rows if r["result"] == "MISS")
    total = len(rows)

    status, accuracy = judge_status(total, hit, miss)

    conn.close()

    return {
        "status": status,
        "total": total,
        "hit": hit,
        "miss": miss,
        "accuracy": round(accuracy, 3)
    }
