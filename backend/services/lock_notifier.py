# backend/services/lock_notifier.py
import os
from datetime import datetime
from typing import Optional

from backend.services.slack_client import SlackClient


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def notify_lock_with_pdf(
    *,
    pdf_bytes: Optional[bytes],
    lock_reason: str,
    lock_level: str = "RED",
    window: str = "rolling",
    details: Optional[str] = None,
) -> None:
    """
    - LOCK 상태는 이미 DB에 반영된 '후' 이 함수가 호출되는 것을 전제로 함
    - 실패해도 예외를 밖으로 올려서 LOCK을 롤백시키면 안 됨 (호출부에서 swallow)
    """
    base_url = os.getenv("APP_BASE_URL", "").strip()
    client = SlackClient()

    header = f"🚨 LOCK 발생 ({lock_level}) | {_now_str()}"
    body = f"사유: {lock_reason}\n윈도우: {window}"
    if details:
        body += f"\n상세: {details}"
    if base_url:
        body += f"\n대시보드: {base_url}"

    text = f"{header}\n{body}"

    # PDF가 있으면 파일 업로드(첨부), 없으면 메시지만
    if pdf_bytes and len(pdf_bytes) > 0:
        filename = f"kpi_report_LOCK_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        client.upload_file(filename=filename, file_bytes=pdf_bytes, initial_comment=text)
    else:
        client.post_message(text=text)
