# backend/routes/admin.py
from fastapi import APIRouter, Request, HTTPException
import os
from backend.services.operation_guard import (
    get_status,
    set_run_mode,
    set_force_pass
)

router = APIRouter(prefix="/api/admin", tags=["admin"])

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

def auth(req: Request):
    token = req.headers.get("x-admin-token")
    if token != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="unauthorized")

@router.get("/status")
def status(req: Request):
    auth(req)
    return get_status()

@router.post("/run-mode/{mode}")
def run_mode(mode: str, req: Request):
    auth(req)
    if mode not in ("paused", "active"):
        raise HTTPException(400, "invalid mode")
    set_run_mode(mode)
    return get_status()

@router.post("/force-pass/{flag}")
def force_pass(flag: str, req: Request):
    auth(req)
    if flag == "on":
        set_force_pass(True)
    elif flag == "off":
        set_force_pass(False)
    else:
        raise HTTPException(400, "invalid flag")
    return get_status()
