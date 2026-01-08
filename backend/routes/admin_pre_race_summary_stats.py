from fastapi import APIRouter
from backend.services.db import get_conn

router = APIRouter(prefix="/api/admin/pre-race", tags=["admin-pre-race"])

@router.get("/summary-stats")
def get_pre_race_summary_stats(limit: int = 50):
    conn = get_conn()
    cur = conn.cursor()

    row = cur.execute("""
    WITH recent AS (
      SELECT *
      FROM pre_race_run_history
      ORDER BY run_at DESC
      LIMIT ?
    )
    SELECT
      COUNT(*) AS total_runs,
      SUM(CASE WHEN bet_pass='BET' THEN 1 ELSE 0 END) AS bet_count,
      SUM(CASE WHEN bet_pass='PASS' THEN 1 ELSE 0 END) AS pass_count,
      ROUND(AVG(confidence), 3) AS avg_confidence,
      ROUND(
        SUM(CASE WHEN bet_pass='BET' AND hit_miss='HIT' THEN 1 ELSE 0 END) * 1.0 /
        NULLIF(SUM(CASE WHEN bet_pass='BET' THEN 1 ELSE 0 END), 0), 3
      ) AS bet_hit_rate
    FROM recent;
    """, (limit,)).fetchone()

    return dict(row) if row else {}
