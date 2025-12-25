from fastapi import APIRouter
from backend.db.conn import get_conn

router = APIRouter(prefix="/api/kpi", tags=["kpi"])

@router.get("/summary")
def get_kpi_summary():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN result = 'HIT' THEN 1 ELSE 0 END) AS hit,
            SUM(CASE WHEN result = 'MISS' THEN 1 ELSE 0 END) AS miss,
            SUM(CASE WHEN result = 'PASS' THEN 1 ELSE 0 END) AS pass
        FROM (
            SELECT
                CASE
                    WHEN p.decision = 'PASS' THEN 'PASS'
                    WHEN p.decision = a.winner THEN 'HIT'
                    ELSE 'MISS'
                END AS result
            FROM predictions p
            LEFT JOIN race_actuals a
                ON p.race_id = a.race_id
        )
    """)

    row = cur.fetchone()
    conn.close()

    total, hit, miss, pas = row

    accuracy_ex_pass = round(hit / (hit + miss), 4) if (hit + miss) > 0 else 0.0
    accuracy_overall = round(hit / total, 4) if total > 0 else 0.0

    return {
        "total": total,
        "hit": hit,
        "miss": miss,
        "pass": pas,
        "accuracy_excluding_pass": accuracy_ex_pass,
        "accuracy_overall": accuracy_overall
    }
