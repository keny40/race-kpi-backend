from fastapi import APIRouter
import sqlite3

DB_PATH = "/tmp/races.db"

router = APIRouter(prefix="/api/kpi", tags=["kpi"])

@router.get("/match")
def get_kpi_match():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    cur.execute("""
        SELECT
            p.race_id,
            p.decision,
            a.winner,
            p.confidence,
            CASE
                WHEN p.decision = a.winner THEN 'HIT'
                ELSE 'MISS'
            END AS result
        FROM predictions p
        LEFT JOIN race_actuals a
          ON p.race_id = a.race_id
        ORDER BY p.created_at DESC
        LIMIT 50
    """)

    rows = cur.fetchall()
    con.close()

    return [dict(r) for r in rows]
