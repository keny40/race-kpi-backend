# backend/routes/admin_control.py
import json
import time
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse

from backend.services.ops_scheduler import (
    scheduler_status,
    scheduler_start,
    scheduler_stop,
    scheduler_run_once,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])

ADMIN_TOKEN = "admin123"

def _auth(request: Request):
    if request.headers.get("x-admin-token") != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")

def _auth_sse(request: Request):
    # EventSource는 기본적으로 커스텀 헤더를 못 넣는 경우가 많아서 query token 지원
    token = request.query_params.get("token", "")
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")

@router.get("/scheduler/status")
def get_status(request: Request):
    _auth(request)
    return scheduler_status()

@router.post("/scheduler/on")
def on(request: Request):
    _auth(request)
    scheduler_start()
    return {"status": "ON"}

@router.post("/scheduler/off")
def off(request: Request):
    _auth(request)
    scheduler_stop()
    return {"status": "OFF"}

@router.post("/scheduler/run")
def run_once(request: Request):
    _auth(request)
    return scheduler_run_once()

@router.get("/scheduler/stream")
def stream(request: Request):
    _auth_sse(request)

    def event_gen():
        last_payload = None
        while True:
            # client disconnect
            if getattr(request, "is_disconnected", None):
                try:
                    if request.is_disconnected():
                        break
                except Exception:
                    pass

            payload = scheduler_status()
            payload_str = json.dumps(payload, ensure_ascii=False)

            # 변경 있을 때만 push (중복 로그 폭주 방지)
            if payload_str != last_payload:
                last_payload = payload_str
                yield f"event: status\ndata: {payload_str}\n\n"

            time.sleep(1)

    return StreamingResponse(event_gen(), media_type="text/event-stream")
