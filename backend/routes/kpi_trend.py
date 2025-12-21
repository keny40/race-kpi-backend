import sqlite3
import os
from fastapi import APIRouter

router = APIRouter()
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "races.db")


def _get_db():
    return sqlite3.connect(DB_PATH)


@router.get("/api/kpi/trend")
def get_kpi_trend(period: str = "month"):
    con = _get_db()
    try:
        cur = con.cursor()
        cur.execute("""
            SELECT substr(p.created_at,1,7) as t,
                   SUM(CASE WHEN p.decision=r.winner THEN 1 ELSE 0 END) as hit,
                   COUNT(*) as total
            FROM predictions p
            LEFT JOIN results r ON p.race_id=r.race_id
            GROUP BY t
            ORDER BY t
        """)
        rows = cur.fetchall()
        return [
            {
                "t": t,
                "hit_rate": round((hit or 0) / max(1, total) * 100, 2)
            }
            for t, hit, total in rows
        ]
    finally:
        con.close()
