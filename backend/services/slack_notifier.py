import os
import requests

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def send_admin_action(action: str, detail: str = ""):
    """
    관리자 액션 Slack 알림
    """
    if not SLACK_WEBHOOK_URL:
        return

    text = f"[ADMIN ACTION]\n• action: {action}\n• detail: {detail}"

    try:
        requests.post(
            SLACK_WEBHOOK_URL,
            json={"text": text},
            timeout=3,
        )
    except Exception:
        # Slack 실패로 서버 죽지 않게
        pass
