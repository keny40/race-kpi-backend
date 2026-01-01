# backend/routes/scheduler_control.py
import json
import time
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.services.ops_scheduler import (
    start,
    stop,
    run_once,
    status,
)

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


@router.post("/on")
def scheduler_on():
    start()
    return {"ok": True}


@router.post("/off")
def scheduler_off():
    stop()
    return {"ok": True}


@router.post("/run")
def scheduler_run_once():
    return run_once()


@router.get("/status")
def scheduler_status():
    return status()


@router.get("/sse")
def scheduler_sse():
    def event_stream():
        while True:
            payload = status()
            yield f"data: {json.dumps(payload)}\n\n"
            time.sleep(1)  # 🔴 이게 핵심 (heartbeat)
    return StreamingResponse(event_stream(), media_type="text/event-stream")
