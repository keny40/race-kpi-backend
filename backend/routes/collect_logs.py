from fastapi import APIRouter, Query
from typing import List, Dict
from datetime import datetime

router = APIRouter(prefix="/api/collect", tags=["collect"])

_COLLECT_LOGS: List[Dict] = []


def _now_iso():
    return datetime.now().isoformat(timespec="seconds")


@router.get("/logs")
def get_collect_logs(limit: int = Query(50, ge=1, le=500)):
    return {
        "items": _COLLECT_LOGS[-limit:][::-1],
        "total": len(_COLLECT_LOGS),
    }


def push_collect_log(log: Dict):
    """
    log 표준 필드 자동 보강
    """
    enriched = {
        "time": log.get("time") or _now_iso(),
        "filename": log.get("filename"),
        "source": log.get("source", "upload"),
        "status": log.get("status", "INFO"),
        "inserted": log.get("inserted"),
        "skipped": log.get("skipped"),
        "count": log.get("count"),
        "race_id": log.get("race_id"),
        "reason": log.get("reason"),
    }

    _COLLECT_LOGS.append(enriched)
