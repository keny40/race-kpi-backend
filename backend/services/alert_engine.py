# backend/services/alert_engine.py

from backend.services.slack_notifier import (
    send_red_alert,
    notify_status_change,
    notify_red_streak,
)


def check_and_auto_force(prev_status, curr_status, red_streak, payload):
    notify_status_change(prev_status, curr_status, payload)
    notify_red_streak(red_streak, 3, payload)

    if curr_status == "RED":
        send_red_alert(payload)
        return True

    return False
