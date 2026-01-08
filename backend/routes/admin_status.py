from fastapi import APIRouter, Request, HTTPException
import os
from backend.services.risk_guard import get_risk_settings

router = APIRouter(prefix="/api/admin/status", tags=["admin-status"])
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")


def _auth(req: Request):
    if req.headers.get("x-admin-token") != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="unauthorized")


@router.get("")
def admin_status(req: Request):
    _auth(req)
    """
    관리자 UI 실시간 상태
    """
    return {
        "guard": get_risk_settings(),
    }
