# backend/routes/admin_status.py
from fastapi import APIRouter, Request, HTTPException
import os
import time

from backend.services.ops_scheduler import status as scheduler_status
from backend.services.risk_guard import get_risk_settings, reset_fail_streak

router = APIRouter(prefix="/api/admin", tags=["admin"])

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")


def _auth(request: Request):
    token = request.headers.get("x-admin-token", "")
    if not ADMIN_PASSWORD or token != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="unauthorized")


@router.get("/status")
def admin_status(request: Request):
    _auth(request)

    sched = scheduler_status()
    risk = get_risk_settings()

    return {
        "scheduler": sched,
        "risk": risk,
        "red_streak": int(risk.get("fail_streak", 0)),
        "paused": bool(risk.get("paused", False)),
        "ts": int(time.time()),
    }


@router.post("/reset_red")
def reset_red(request: Request):
    _auth(request)
    reset_fail_streak()
    return {"ok": True}
