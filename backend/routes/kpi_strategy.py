from fastapi import APIRouter
from backend.db.conn import get_conn

router = APIRouter(prefix="/api/kpi", tags=["kpi"])

@router.get("/strategy")
def get_kpi_by_strategy():
    con = get_conn()
    cur = con.cursor()

    cur.execute("""
        SELECT
            strategy,
            COUNT(*) AS total,
            SUM(CASE WHEN result='HIT' THEN 1 ELSE 0 END) AS hit,
            SUM(CASE WHEN result='MISS' THEN 1 ELSE 0 END) AS miss,
            SUM(CASE WHEN result='PASS' THEN 1 ELSE 0 END) AS pass
        FROM v_race_match_strategy
        GROUP BY strategy
        ORDER BY strategy
    """)

    rows = cur.fetchall()
    con.close()

    out = []
    for s, total, hit, miss, passed in rows:
        acc = round(hit / (hit + miss), 4) if (hit + miss) > 0 else 0.0
        out.append({
            "strategy": s,
            "total": total,
            "hit": hit,
            "miss": miss,
            "pass": passed,
            "accuracy": acc
        })

    return out
