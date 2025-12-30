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
    text = (
        "[ADMIN ACTION]\n"
        f"• action: {action}\n"
        f"• detail: {detail}"
    )
    _post(text)


def send_red_alert(reason: str, score: float | None = None):
    """
    단일 RED 발생 알림
    """
    msg = f"[RED ALERT]\n• reason: {reason}"
    if score is not None:
        msg += f"\n• score: {score}"
    _post(msg)


def notify_status_change(
    prev_status: str,
    new_status: str,
    reason: str | None = None,
):
    """
    시스템 상태 변경 알림
    """
    msg = (
        "[STATUS CHANGE]\n"
        f"• from: {prev_status}\n"
        f"• to: {new_status}"
    )
    if reason:
        msg += f"\n• reason: {reason}"
    _post(msg)


def notify_red_streak(
    count: int,
    threshold: int,
    action: str | None = None,
):
    """
    RED 연속 발생 알림 (자동 PAUSE / FORCE PASS 트리거용)
    """
    msg = (
        "[RED STREAK]\n"
        f"• count: {count}\n"
        f"• threshold: {threshold}"
    )
    if action:
        msg += f"\n• action: {action}"
    _post(msg)
