# backend/services/strategy_state.py

from backend.services.slack_notifier import send_red_alert


def force_pass_with_alert(payload: dict):
    send_red_alert(payload)
