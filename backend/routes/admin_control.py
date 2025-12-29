from fastapi import APIRouter, Request, HTTPException
from backend.services.strategy_state import (
    is_force_pass_enabled,
    force_pass_on,
    force_pass_off
)
from backend.services.admin_log import log_action
import os

router = APIRouter(prefix="/api/admin", tags=["admin-control"])
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

def _auth(request: Request):
    if request.headers.get("x-admin-token") != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="unauthorized")

@router.post("/force-pass/on")
def force_on(request: Request):
    _auth(request)
    force_pass_on()
    log_action("FORCE_PASS_ON", "MANUAL")
    return {"status": "ok", "forced": True}

@router.post("/force-pass/off")
def force_off(request: Request):
    _auth(request)
    force_pass_off()
    log_action("FORCE_PASS_OFF", "MANUAL")
    return {"status": "ok", "forced": False}

@router.get("/force-pass/status")
def force_status(request: Request):
    _auth(request)
    return {"forced": is_force_pass_enabled()}
