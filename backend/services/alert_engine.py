from backend.utils.slack_notifier import send_red_alert

RED_STREAK_THRESHOLD = 3  # N회 연속 기준


def handle_state_transition(prev: dict | None, curr: dict):
    """
    prev: 이전 상태 (없을 수 있음)
    curr: 현재 상태
    """

    # 1️⃣ RED 연속 N회
    if curr["status"] == "RED" and curr["red_streak"] >= RED_STREAK_THRESHOLD:
        send_red_alert(curr)
        return

    # 2️⃣ YELLOW → RED 전이
    if prev and prev["status"] == "YELLOW" and curr["status"] == "RED":
        send_red_alert(curr)
