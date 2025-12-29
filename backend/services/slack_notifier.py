# backend/services/slack_notifier.py
from backend.services.slack_notifier import (
    _post_webhook,
    send_red_pdf_bundle,
)

def send_red_alert(payload: dict):
    """
    alert_engine에서 호출하는 표준 인터페이스
    """
    # 텍스트 요약
    status = payload.get("status")
    reason = payload.get("reason", "")
    _post_webhook(f"🚨 KPI ALERT\n상태: {status}\n사유: {reason}")

    # PDF 번들 전송 (기존 로직 재사용)
    send_red_pdf_bundle()
