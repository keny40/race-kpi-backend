import os
from backend.services.strategy_state import (
    is_force_pass_enabled,
    force_pass_off,
)
from backend.services.admin_log import log_admin_action

GREEN_RELEASE_COUNT = int(os.getenv("FORCE_PASS_RELEASE_GREEN_COUNT", "3"))

_green_streak = 0

def check_and_auto_release(kpi_status: str):
    """
    FORCE PASS 상태에서
    - KPI GREEN 연속 N회 → FORCE PASS 자동 해제
    """
    global _green_streak

    if not is_force_pass_enabled():
        _green_streak = 0
        return False

    if kpi_status == "GREEN":
        _green_streak += 1
        if _green_streak >= GREEN_RELEASE_COUNT:
            force_pass_off()
            log_admin_action(
                "FORCE_PASS_OFF",
                f"AUTO_GREEN_{_green_streak}"
            )
            _green_streak = 0
            return True
    else:
        _green_streak = 0

    return False
