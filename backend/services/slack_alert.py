import os
import json
import requests
from datetime import datetime

from backend.services.pdf_red_report import build_red_report_pdf

# -----------------------------
# 환경변수
# -----------------------------
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def _post(payload: dict):
    if not SLACK_WEBHOOK_URL:
        # 운영 중 Slack 미설정이어도 서버는 죽지 않게
        print("[WARN] SLACK_WEBHOOK_URL not set")
        return

    res = requests.post(
        SLACK_WEBHOOK_URL,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
        timeout=5,
    )
    res.raise_for_status()


# --------------------------------------------------
# 1️⃣ RED 연속/가중치 경고 (PDF 포함)
# --------------------------------------------------
def send_red_alert_with_pdf(reason: str):
    """
    RED 잠금 발생 시 호출
    - PDF 생성
    - Slack에 링크/안내 메시지 전송
    """
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # PDF 생성
    pdf_path = build_red_report_pdf()

    text = (
        ":rotating_light: *RED SYSTEM LOCK DETECTED*\n"
        f"> Reason: `{reason}`\n"
        f"> Time: `{ts}`\n"
        f"> PDF generated at: `{pdf_path}`"
    )

    payload = {
        "text": text
    }

    _post(payload)


# --------------------------------------------------
# 2️⃣ 일일 요약 (B-4 스케줄러)
# --------------------------------------------------
def send_daily_summary():
    """
    하루 1회 Slack 요약
    """
    ts = datetime.utcnow().strftime("%Y-%m-%d")

    payload = {
        "text": f":bar_chart: *Daily KPI Summary* ({ts})\n자동 리포트 전송 완료"
    }

    _post(payload)
