from fastapi import APIRouter
from backend.services.db import get_conn

router = APIRouter(prefix="/api/admin/pre-race", tags=["admin-pre-race-kpi"])

@router.get("/kpi-result")
def kpi_result():
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            h.confidence,
            h.decision,
            a.winner,
            json_extract(h.summary_json, '$.top_horses[0].horse_no') AS pick
        FROM pre_race_run_history h
        JOIN actual_results a ON h.race_id = a.race_id
        WHERE h.decision = 'BET'
    """).fetchall()

    total = len(rows)
    hit = sum(1 for r in rows if str(r["pick"]) == str(r["winner"]))

    return {
        "total_bet": total,
        "hit": hit,
        "hit_rate": round(hit / total, 3) if total else 0
    }
