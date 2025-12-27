# backend/services/slack_notify.py
import os
import json
import tempfile
from datetime import datetime, timezone, timedelta

import requests

KST = timezone(timedelta(hours=9))

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")  # 있으면 PDF 파일 업로드 가능
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#alerts")

# PDF 엔드포인트는 내부 함수 호출 대신 파일 생성 모듈을 직접 호출
from backend.routes.kpi_report import build_kpi_pdf  # kpi_report.py에 존재한다고 가정


def _post_webhook(text: str):
    if not SLACK_WEBHOOK_URL:
        return
    requests.post(
        SLACK_WEBHOOK_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps({"text": text}),
        timeout=15,
    )


def _upload_file(filepath: str, title: str):
    """
    Slack Incoming Webhook은 바이너리 첨부가 안 됩니다
    SLACK_BOT_TOKEN이 있으면 files.upload로 PDF 첨부
    """
    if not SLACK_BOT_TOKEN:
        return False

    with open(filepath, "rb") as f:
        resp = requests.post(
            "https://slack.com/api/files.upload",
            headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
            data={"channels": SLACK_CHANNEL, "title": title},
            files={"file": f},
            timeout=30,
        )
    try:
        data = resp.json()
        return bool(data.get("ok"))
    except Exception:
        return False


def _fmt(payload: dict) -> str:
    return (
        f"[KPI] status={payload.get('status')}  "
        f"total={payload.get('total')}  hit={payload.get('hit')}  miss={payload.get('miss')}  "
        f"acc={payload.get('accuracy')}"
    )


def maybe_notify_status_change(prev_status: str, curr_status: str, payload: dict):
    # 2) YELLOW -> RED 전이 알림
    if prev_status == "YELLOW" and curr_status == "RED":
        _post_webhook(f"⚠️ YELLOW → RED 전이 감지\n{_fmt(payload)}")


def maybe_notify_red_streak(red_streak: int, n: int, payload: dict):
    # 1) RED 연속 N회일 때만 알림
    if n <= 0:
        return
    if payload.get("status") != "RED":
        return
    if red_streak == n:
        _post_webhook(f"🚨 RED 연속 {n}회 도달\n{_fmt(payload)}")


def send_daily_summary(payload: dict):
    # 3) 하루 1회 요약 리포트 Slack 발송
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    _post_webhook(f"📌 일일 요약 리포트 ({now})\n{_fmt(payload)}")


def send_red_pdf_bundle():
    """
    B-5: RED 시 PDF 자동 첨부 + 안내
    - SLACK_BOT_TOKEN 있으면 파일 업로드
    - 없으면 텍스트만 전송
    """
    _post_webhook("🚫 KPI가 RED 상태입니다. 예측은 PASS로 강제 처리됩니다. PDF 리포트를 생성합니다.")

    # PDF 생성
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "kpi_red_report.pdf")
        build_kpi_pdf(path)

        ok = _upload_file(path, "KPI RED Report")
        if ok:
            _post_webhook("✅ KPI RED 리포트 PDF 업로드 완료")
        else:
            _post_webhook("ℹ️ PDF 업로드는 SLACK_BOT_TOKEN 설정 시 가능 (현재는 텍스트 알림만 전송)")
