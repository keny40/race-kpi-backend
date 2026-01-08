# backend/routes/race_decision.py
import os
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from backend.services.race_decision import (
    get_threshold_settings,
    set_threshold_mode,
    set_manual_threshold,
    compute_race_decisions,
    get_race_decisions,
)

router = APIRouter(prefix="/api/race", tags=["race-decision"])

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

def _auth_admin(request: Request):
    token = request.headers.get("x-admin-token", "")
    if not ADMIN_PASSWORD or token != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="unauthorized")

# ---- public ----
@router.get("/decision")
def api_get_decision(race_id: str = Query(...)):
    """
    저장된 decision 조회
    """
    return get_race_decisions(race_id)

@router.post("/decision/compute")
def api_compute_decision(race_id: str = Query(...)):
    """
    현재 threshold 기준으로 decision 재계산 + 저장
    """
    return compute_race_decisions(race_id)

@router.get("/threshold")
def api_threshold():
    return {"ok": True, "settings": get_threshold_settings()}

# ---- admin ----
class ThresholdReq(BaseModel):
    threshold_mode: str | None = None   # manual/auto
    manual_threshold: float | None = None

@router.post("/admin/threshold")
def api_set_threshold(request: Request, body: ThresholdReq):
    """
    관리자: 기준선 설정
    - mode=manual/auto
    - manual_threshold=0~1
    """
    _auth_admin(request)

    out = {"ok": True, "changed": {}}
    if body.threshold_mode is not None:
        out["changed"]["threshold_mode"] = set_threshold_mode(body.threshold_mode)
    if body.manual_threshold is not None:
        out["changed"]["manual_threshold"] = set_manual_threshold(body.manual_threshold)

    out["settings"] = get_threshold_settings()
    return out
