from fastapi import APIRouter
from backend.db.conn import get_conn

router = APIRouter(prefix="/api/kpi", tags=["kpi"])

@router.get("/match")
def get_kpi_match():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            p.race_id,
            p.decision,
            p.confidence,
            a.winner,
            CASE
                WHEN p.decision = 'PASS' THEN 'PASS'
                WHEN p.decision = a.winner THEN 'HIT'
                ELSE 'MISS'
            END AS result,
            p.created_at
        FROM predictions p
        LEFT JOIN race_actuals a
            ON p.race_id = a.race_id
        ORDER BY p.created_at DESC
        LIMIT 50
    """)

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "race_id": r[0],
            "decision": r[1],
            "confidence": r[2],
            "winner": r[3],
            "result": r[4],
            "time": r[5]
        }
        for r in rows
    ]
