from fastapi import APIRouter
from backend.services.alert_engine import check_and_auto_force

router = APIRouter(prefix="/api/alert", tags=["alert"])

@router.post("/red-check")
def red_check(red_count: int):
    triggered = check_and_auto_force(red_count)
    return {
        "auto_force_pass": triggered,
        "red_count": red_count
    }
