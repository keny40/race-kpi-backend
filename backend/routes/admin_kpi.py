from fastapi import APIRouter, Request, HTTPException, Query
import os
from backend.services.db import get_conn

router = APIRouter(prefix="/api/admin/kpi", tags=["admin-kpi"])

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")


def _auth(request: Request):
    token = request.headers.get("x-admin-token", "")
    if not ADMIN_PASSWORD or token != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="unauthorized")


@router.get("/run_only")
def admin_kpi_run_only(request: Request, limit: int = Query(50, ge=1, le=500)):
    """
    관리자용 RUN 전용 KPI
    - passed=0만 조회
    """
    _auth(request)
    conn = get_conn()
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT id, race_id, predicted_horse_no, confidence, passed, created_at
          FROM predictions
         WHERE passed=0
         ORDER BY id DESC
         LIMIT ?
        """,
        (int(limit),),
    ).fetchall()

    total_run = cur.execute(
        "SELECT COUNT(*) AS c FROM predictions WHERE passed=0"
    ).fetchone()["c"] or 0

    conn.close()

    return {
        "filters": {"passed": 0},
        "total_run": int(total_run),
        "rows": [
            {
                "id": int(r["id"]),
                "race_id": r["race_id"],
                "predicted_horse_no": r["predicted_horse_no"],
                "confidence": r["confidence"],
                "passed": int(r["passed"]),
                "created_at": r["created_at"],
            }
            for r in rows
        ],
    }
