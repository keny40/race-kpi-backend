import os
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import StreamingResponse, FileResponse

from backend.services.strategy_state import (
    enable_force_pass,
    disable_force_pass,
    is_force_pass_enabled,
)
from backend.services.admin_log import log_admin_action, get_logs
from backend.services.slack_notifier import send_admin_action
from backend.services.pdf_generator import generate_admin_log_pdf
from backend.services.state_guard import get_run_mode, set_run_mode, is_paused

router = APIRouter(prefix="/api/admin", tags=["admin-control"])

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

def _auth(request: Request):
    if not ADMIN_PASSWORD:
        return
    token = request.headers.get("x-admin-token", "")
    if token != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="unauthorized")

@router.get("/status")
def status(request: Request):
    _auth(request)
    return {
        "force_pass": is_force_pass_enabled(),
        "run_mode": get_run_mode(),
        "paused": is_paused(),
    }

@router.post("/force-pass/on")
def force_pass_on(request: Request):
    _auth(request)
    enable_force_pass(reason="MANUAL")
    log_admin_action("FORCE_PASS_ON", "manual")
    send_admin_action("FORCE_PASS_ON", "manual")
    return {"status": "ok", "force_pass": True}

@router.post("/force-pass/off")
def force_pass_off(request: Request):
    _auth(request)
    disable_force_pass()
    log_admin_action("FORCE_PASS_OFF", "manual")
    send_admin_action("FORCE_PASS_OFF", "manual")
    return {"status": "ok", "force_pass": False}

# === 운영 가드: PAUSED/ACTIVE 토글 ===
@router.post("/run-mode/paused")
def set_paused(request: Request):
    _auth(request)
    set_run_mode("PAUSED")
    log_admin_action("RUN_MODE", "PAUSED")
    send_admin_action("RUN_MODE", "PAUSED")
    return {"status": "ok", "run_mode": "PAUSED", "paused": True}

@router.post("/run-mode/active")
def set_active(request: Request):
    _auth(request)
    set_run_mode("ACTIVE")
    log_admin_action("RUN_MODE", "ACTIVE")
    send_admin_action("RUN_MODE", "ACTIVE")
    return {"status": "ok", "run_mode": "ACTIVE", "paused": False}

@router.get("/logs")
def logs(request: Request, limit: int = Query(100, ge=1, le=1000)):
    _auth(request)
    return get_logs(limit=limit)

@router.get("/logs.csv")
def logs_csv(request: Request, limit: int = Query(500, ge=1, le=5000)):
    _auth(request)
    rows = get_logs(limit=limit)

    def gen():
        yield "created_at,action,detail\n"
        for r in rows:
            ca = str(r.get("created_at", "")).replace("\n", " ").replace(",", " ")
            ac = str(r.get("action", "")).replace("\n", " ").replace(",", " ")
            de = str(r.get("detail", "")).replace("\n", " ").replace(",", " ")
            yield f"{ca},{ac},{de}\n"

    return StreamingResponse(
        gen(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=admin_logs.csv"},
    )

@router.get("/logs.pdf")
def logs_pdf(request: Request, limit: int = Query(300, ge=1, le=3000)):
    _auth(request)
    rows = get_logs(limit=limit)
    path = generate_admin_log_pdf(rows)
    return FileResponse(path, media_type="application/pdf", filename="admin_logs.pdf")
