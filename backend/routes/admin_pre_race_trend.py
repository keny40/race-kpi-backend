# backend/routes/admin_pre_race_trend.py
from fastapi import APIRouter
from backend.services.db import get_conn

router = APIRouter(prefix="/api/admin/pre-race", tags=["admin-pre-race-trend"])

@router.get("/trend")
def trend():
    conn = get_conn()
    rows = conn.execute("""
      SELECT
        substr(run_at,1,7) AS ym,
        COUNT(*) AS n,
        AVG(confidence) AS avg_conf
      FROM pre_race_run_history
      GROUP BY ym
      ORDER BY ym
    """).fetchall()

    return {
      "items":[{"ym":r["ym"],"count":r["n"],"avg_confidence":round(r["avg_conf"],3)} for r in rows]
    }
