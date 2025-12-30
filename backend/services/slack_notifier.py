import os
import requests

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def _post(text: str):
    if not SLACK_WEBHOOK_URL:
        return
    try:
        requests.post(
            SLACK_WEBHOOK_URL,
            json={"text": text},
            timeout=3,
        )
    except Exception:
        pass


def send_admin_action(action: str, detail: str = ""):
    """
    관리자 수동 액션 알림
    """
    text = f"[ADMIN ACTION]\n• action: {action}\n• detail: {detail}"
    _post(text)


def send_red_alert(reason: str, score: float | None = None):
    """
    RED 상태 자동 경고 알림
    """
    msg = f"[RED ALERT]\n• reason: {reason}"
    if score is not None:
        msg += f"\n• score: {score}"
    _post(msg)
