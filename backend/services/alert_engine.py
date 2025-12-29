from backend.services.strategy_state import (
    is_force_pass_enabled,
    force_pass,
    force_pass_off,
)
from backend.services.slack_notifier import send_red_alert


def check_and_auto_force(kpi_summary: dict) -> bool:
    """
    KPI 상태 기반 자동 FORCE PASS 제어
    - RED  → FORCE PASS ON
    - GREEN → FORCE PASS OFF
    반환값: 상태 변경 여부
    """

    status = kpi_summary.get("status")
    reason = kpi_summary.get("reason", "")

    # ===============================
    # RED → FORCE PASS ON
    # ===============================
    if status == "RED":
        if not is_force_pass_enabled():
            force_pass(reason="AUTO_RED")
            send_red_alert(kpi_summary)
            return True
        return False

    # ===============================
    # GREEN → FORCE PASS OFF
    # ===============================
    if status == "GREEN":
        if is_force_pass_enabled():
            force_pass_off()
            return True
        return False

    # YELLOW / 기타 상태
    return False
