# backend/routes/admin_scheduler.py

from fastapi import APIRouter, Request, HTTPException, Response
from backend.services.ops_scheduler import (
    start_scheduler, stop_scheduler, run_once, reset_red_state, configure
)
from backend.services.admin_audit import log_action, list_actions
import os
import csv
import io

router = APIRouter(prefix="/api/admin", tags=["admin"])

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

def _auth(req: Request):
    if req.headers.get("x-admin-token") != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="unauthorized")

def _ok(action, msg=""):
    log_action(action, "ok", msg)
    return {"status": "ok"}

def _fail(action, e):
    log_action(action, "fail", str(e))
    raise HTTPException(500, "Internal Server Error")

@router.post("/scheduler/on")
def on(req: Request):
    _auth(req)
    try:
        return start_scheduler()
    except Exception as e:
        _fail("SCHEDULER_ON", e)

@router.post("/scheduler/off")
def off(req: Request):
    _auth(req)
    try:
        return stop_scheduler()
    except Exception as e:
        _fail("SCHEDULER_OFF", e)

@router.post("/scheduler/run")
def run(req: Request):
    _auth(req)
    try:
        return run_once()
    except Exception as e:
        _fail("SCHEDULER_RUN", e)

@router.post("/reset_red")
def reset_red(req: Request):
    _auth(req)
    try:
        res = reset_red_state()
        log_action("RESET_RED", "ok", str(res))
        return res
    except Exception as e:
        _fail("RESET_RED", e)

@router.get("/scheduler/logs")
def logs(req: Request, limit: int = 200, format: str = "json"):
    _auth(req)
    rows = list_actions(limit)

    if format == "csv":
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        return Response(
            buf.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=admin_logs.csv"}
        )

    return {"status": "ok", "rows": rows}
