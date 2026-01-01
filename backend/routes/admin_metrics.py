# backend/routes/admin_metrics.py
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
import os
import csv
import io
import json

from backend.services.log_store import query_logs, query_logs_csv, query_red_history, insert_log
from backend.services.risk_guard import reset_red_streak
from backend.services.ops_scheduler import start_scheduler, stop_scheduler, run_once

router = APIRouter(prefix="/api/admin", tags=["admin"])

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")


def _auth(request: Request):
    token = request.headers.get("x-admin-token", "")
    if not ADMIN_PASSWORD or token != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="unauthorized")


@router.get("/logs")
def get_logs(
    request: Request,
    actions: str = Query("", description="comma separated ex: RUN,RESET,FAIL"),
    levels: str = Query("", description="comma separated ex: INFO,WARN,ERROR"),
    limit: int = Query(200, ge=1, le=2000),
    offset: int = Query(0, ge=0),
):
    _auth(request)
    a = [x.strip() for x in actions.split(",") if x.strip()] or None
    l = [x.strip() for x in levels.split(",") if x.strip()] or None
    rows = query_logs(actions=a, levels=l, limit=limit, offset=offset)
    return {"items": rows, "limit": limit, "offset": offset}


@router.get("/logs.csv")
def get_logs_csv(
    request: Request,
    actions: str = Query("", description="comma separated ex: RUN,RESET,FAIL"),
    levels: str = Query("", description="comma separated ex: INFO,WARN,ERROR"),
    limit: int = Query(5000, ge=1, le=20000),
):
    _auth(request)
    a = [x.strip() for x in actions.split(",") if x.strip()] or None
    l = [x.strip() for x in levels.split(",") if x.strip()] or None
    rows = query_logs_csv(actions=a, levels=l, limit=limit)

    def iter_csv():
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["id", "ts", "action", "level", "detail_json"])
        yield buf.getvalue()
        buf.seek(0)
        buf.truncate(0)

        for r in rows:
            w.writerow([r["id"], r["ts"], r["action"], r["level"], r["detail_json"]])
            yield buf.getvalue()
            buf.seek(0)
            buf.truncate(0)

    headers = {"Content-Disposition": "attachment; filename=ops_logs.csv"}
    return StreamingResponse(iter_csv(), media_type="text/csv; charset=utf-8", headers=headers)


@router.get("/red_history")
def get_red_history(
    request: Request,
    bucket: str = Query("hour", pattern="^(hour|day)$"),
    days: int = Query(3, ge=1, le=30),
):
    _auth(request)
    return query_red_history(bucket=bucket, days=days)


# (선택) 기존 관리자 버튼들이 여기 붙어있다면 그대로 써도 되고
# 아래 endpoint를 UI에서 바로 호출해도 됩니다

@router.post("/scheduler/start")
def api_start(request: Request):
    _auth(request)
    insert_log("ON", {})
    return start_scheduler()

@router.post("/scheduler/stop")
def api_stop(request: Request):
    _auth(request)
    insert_log("OFF", {})
    return stop_scheduler()

@router.post("/scheduler/run_once")
def api_run_once(request: Request):
    _auth(request)
    return run_once()

@router.post("/reset_red")
def api_reset_red(request: Request):
    _auth(request)
    return reset_red_streak()
