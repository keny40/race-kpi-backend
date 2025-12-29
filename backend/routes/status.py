# backend/routes/status.py
from fastapi import APIRouter
from backend.services.strategy_state import is_force_pass_enabled
from backend.services.kpi_state import get_kpi_status, get_kpi_reason
from backend.services.admin_log import get_last_admin_log

router = APIRouter(prefix="/api/status", tags=["status"])

@router.get("/overview")
def status_overview():
    return {
        "kpi_status": get_kpi_status(),
        "kpi_reason": get_kpi_reason(),
        "force_pass": is_force_pass_enabled(),
        "last_admin_action": get_last_admin_log()
    }
