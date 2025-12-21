from fastapi import APIRouter
from datetime import datetime
from typing import Literal

router = APIRouter()

TIMELINE: list[dict] = []

def log_event(
    event_type: Literal["exists", "predict", "feedback"],
    race_id: str | None,
    payload: dict
):
    TIMELINE.append({
        "type": event_type,
        "race_id": race_id,
        "payload": payload,
        "timestamp": datetime.utcnow().isoformat()
    })

@router.get("/metrics/timeline")
def get_timeline(limit: int = 100):
    return {
        "items": TIMELINE[-limit:][::-1]
    }
