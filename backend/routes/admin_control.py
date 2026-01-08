# backend/routes/admin_control.py
from fastapi import APIRouter, Request, HTTPException
import os

from backend.services.ops_scheduler import start_scheduler, stop_scheduler
from backend.services.log_store import insert_log

router = APIRouter(prefix="/api/admin", tags=["admin-control"])

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")


def _auth(request: Request):
    token = request.headers.get("x-admin-token", "")
    if not ADMIN_PASSWORD or token != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="unauthorized")


@router.post("/scheduler/start")
def scheduler_start(request: Request):
    _auth(request)
    start_scheduler()
    insert_log("SCHEDULER_START", {})
    return {"ok": True, "state": "STARTED"}


@router.post("/scheduler/stop")
def scheduler_stop(request: Request):
    _auth(request)
    stop_scheduler()
    insert_log("SCHEDULER_STOP", {})
    return {"ok": True, "state": "STOPPED"}
