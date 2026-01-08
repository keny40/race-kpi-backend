from fastapi import APIRouter, Request, HTTPException
import os

from backend.services.pre_race_scheduler import (
    start_scheduler,
    stop_scheduler,
    get_status,
)

router = APIRouter(prefix="/api/admin/scheduler", tags=["admin-scheduler"])

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")


def _auth(request: Request):
    token = request.headers.get("x-admin-token", "")
    if token != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="unauthorized")


@router.get("/status")
def scheduler_status(request: Request):
    _auth(request)
    return get_status()


@router.post("/start")
def scheduler_start(request: Request):
    _auth(request)
    return start_scheduler()


@router.post("/stop")
def scheduler_stop(request: Request):
    _auth(request)
    return stop_scheduler()
