# backend/services/slack_notify.py
import requests
import os
import json

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

def _post(text: str):
    if not SLACK_WEBHOOK_URL:
        return
    payload = {"text": text}
    requests.post(
        SLACK_WEBHOOK_URL,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
        timeout=3,
    )

# =========================
# 기존 코드 호환용 함수명
# =========================

def send_red_alert(reason: dict | str):
    if isinstance(reason, dict):
        text = (
            "🔴 RED 발생\n"
            f"- score: {reason.get('score')}\n"
            f"- streak: {reason.get('streak')}\n"
            f"- feature: {reason.get('feature')}"
        )
    else:
        text = f"🔴 RED 발생\n- {reason}"
    _post(text)

def send_reset_notice():
    _post("🟢 RED RESET (운영자 조치)")

def send_recover_notice():
    _post("✅ 시스템 정상 복귀")

# =========================
# 신규 코드에서 쓰는 별칭
# =========================

def send_text(text: str):
    _post(text)

def notify_red(reason: dict):
    send_red_alert(reason)

def notify_reset():
    send_reset_notice()

def notify_recover():
    send_recover_notice()
