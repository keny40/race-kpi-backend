from fastapi import APIRouter
from backend.services.strategy_state import is_force_pass_enabled

router = APIRouter(prefix="/api/status", tags=["status"])

@router.get("/overview")
def overview():
    if is_force_pass_enabled():
        return {
            "status": "FORCE_PASS"
        }
    return {
        "status": "NORMAL"
    }
