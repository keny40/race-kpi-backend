from datetime import datetime
from backend.services.strategy_state import (
    is_force_pass_enabled,
    force_pass,
    force_pass_off,
    get_system_value,
    set_system_value,
)
from backend.services.admin_log import log_admin_action
from backend.services.slack_notifier import send_red_alert


# ===============================
# KPI 상태 기반 자동 FORCE PASS
# ===============================

def check_and_auto_force(kpi_summary: dict) -> bool:
    """
    KPI 결과를 기반으로
    - RED → FORCE PASS 자동 ON
    - GREEN N회 → FORCE PASS 자동 OFF
    반환값: 상태 변경 여부
    """

    status = kpi_summary.get("status")
    reason = kpi_summary.get("reason", "")

    # 현재 상태 카운터
    red_streak = int(get_system_value("red_streak", 0))
    green_streak = int(get_system_value("green_streak", 0))

    # 임계치
    red_threshold = int(get_system_value("red_notify_n", 3))
    green_threshold = int(get_system_value("green_release_n", 3))

    changed = False

    # ===============================
    # RED 처리
    # ===============================
    if status == "RED":
        red_streak += 1
        green_streak = 0

        set_system_value("red_streak", red_streak)
        set_system_value("green_streak", 0)

        if red_streak >= red_threshold:
            if not is_force_pass_enabled():
                force_pass(reason="AUTO_RED")
                log_admin_action("FORCE_PASS_ON", "AUTO_RED")
                send_red_alert(kpi_summary)
                changed = True

        return changed

    # ===============================
    # GREEN 처리
    # ===============================
    if status == "GREEN":
        green_streak += 1
        red_streak = 0

        set_system_value("green_streak", green_streak)
        set_system_value("red_streak", 0)

        if green_streak >= green_threshold:
            if is_force_pass_enabled():
                force_pass_off()
                log_admin_action("FORCE_PASS_OFF", "AUTO_GREEN")
                changed = True

        return changed

    # ===============================
    # YELLOW / 기타
    # ===============================
    set_system_value("red_streak", 0)
    set_system_value("green_streak", 0)

    return False
