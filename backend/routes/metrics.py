from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

EXISTS_LOGS = []

class ExistsCheckLog(BaseModel):
    race_id: str
    exists: bool
    count: int
    timestamp: datetime | None = None

@router.post("/metrics/exists-check")
def log_exists_check(payload: ExistsCheckLog):
    payload.timestamp = datetime.utcnow()
    EXISTS_LOGS.append(payload.dict())
    return {"ok": True}

@router.get("/metrics/exists-timeline")
def exists_timeline(limit: int = 50):
    return {
        "items": EXISTS_LOGS[-limit:][::-1]
    }

STREAK_LOGS = []

@router.post("/metrics/streak-log")
def log_streak(payload: dict):
    STREAK_LOGS.append(payload)
    return {"ok": True}

@router.get("/metrics/streak-log")
def get_streak_logs(limit: int = 100):
    return {"items": STREAK_LOGS[-limit:][::-1]}
