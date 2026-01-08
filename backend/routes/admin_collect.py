# backend/routes/admin_collect.py
import os
from fastapi import APIRouter, Request, HTTPException
from backend.services.kra_collector import collect_once, get_config_from_env
from backend.services.kra_collect_scheduler import start as sched_start, stop as sched_stop, is_running as sched_running

router = APIRouter(prefix="/api/admin/collect", tags=["admin-collect"])

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")


def _auth(request: Request):
    token = request.headers.get("x-admin-token", "")
    if not ADMIN_PASSWORD or token != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="unauthorized")


def _db_path() -> str:
    return os.getenv("DB_PATH", os.path.join(os.getcwd(), "backend", "races.db"))


@router.get("/status")
def status(request: Request):
    _auth(request)
    cfg = get_config_from_env()
    return {
        "ok": True,
        "scheduler_running": bool(sched_running()),
        "env": {
            "KRA_COLLECT_ENABLED": cfg.enabled,
            "KRA_COLLECT_MODE": cfg.mode,
            "KRA_RACES_URL_set": bool(cfg.races_url),
        },
    }


@router.post("/run_once")
def run_once(request: Request):
    _auth(request)
    cfg = get_config_from_env()
    res = collect_once(_db_path(), cfg)
    return res


@router.post("/scheduler/start")
def start_scheduler(request: Request):
    _auth(request)
    ok = sched_start()
    return {"ok": True, "started": bool(ok), "running": bool(sched_running())}


@router.post("/scheduler/stop")
def stop_scheduler(request: Request):
    _auth(request)
    sched_stop()
    return {"ok": True, "running": bool(sched_running())}
