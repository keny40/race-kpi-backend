from fastapi import APIRouter, Query
from backend.services.admin_state import set_state, get_state
from backend.services.admin_log import fetch_admin_logs

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/state/{key}")
def set_admin_state(key: str, enabled: bool):
    set_state(key, enabled)
    return {"key": key, "enabled": enabled}


@router.get("/state/{key}")
def get_admin_state(key: str):
    return {"key": key, "enabled": get_state(key)}


@router.get("/logs")
def get_admin_logs(
    limit: int = Query(50, ge=1, le=500),
    action: str | None = None,
    admin_id: str | None = None,
    since: str | None = None
):
    return {
        "items": fetch_admin_logs(
            limit=limit,
            action=action,
            admin_id=admin_id,
            since=since
        )
    }
