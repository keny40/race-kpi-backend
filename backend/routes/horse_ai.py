# backend/routes/horse_ai.py
import os
from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel

from backend.services.horse_ai import (
    init_horse_tables,
    load_horse_profile_xlsx,
    load_horse_performance_xlsx,
    compute_and_store_horse_scores,
    get_top_horse_scores,
    get_horse_score,
)

router = APIRouter(prefix="/api/horse", tags=["horse-ai"])

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

def _auth_admin(request: Request):
    token = request.headers.get("x-admin-token", "")
    if not ADMIN_PASSWORD or token != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="unauthorized")

class LoadReq(BaseModel):
    profile_xlsx_path: str
    performance_xlsx_path: str | None = None
    period_from: str | None = None
    period_to: str | None = None

@router.post("/admin/load")
def admin_load(request: Request, body: LoadReq):
    """
    관리자 전용:
    - profile/performance xlsx를 DB에 적재
    """
    _auth_admin(request)

    init_horse_tables(None)
    r1 = load_horse_profile_xlsx(body.profile_xlsx_path, None)
    r2 = None
    if body.performance_xlsx_path:
        r2 = load_horse_performance_xlsx(
            body.performance_xlsx_path,
            period_from=body.period_from,
            period_to=body.period_to,
            db_path=None
        )
    return {"ok": True, "profile": r1, "performance": r2}

@router.post("/admin/score/recompute")
def admin_recompute_scores(request: Request):
    """
    관리자 전용:
    - 말별 점수 재계산 후 horse_scores에 저장
    """
    _auth_admin(request)
    return compute_and_store_horse_scores(None)

@router.get("/scores")
def list_scores(limit: int = Query(50, ge=1, le=500)):
    """
    공개:
    - 말별 점수 상위 N
    """
    return {"ok": True, "items": get_top_horse_scores(limit=limit, db_path=None)}

@router.get("/score")
def one_score(name: str = Query(..., description="horse_name")):
    """
    공개:
    - 말 1마리 점수
    """
    row = get_horse_score(name, db_path=None)
    if not row:
        raise HTTPException(status_code=404, detail="horse not found")
    return {"ok": True, "item": row}
