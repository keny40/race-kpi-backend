# backend/services/slack_notifier.py

import os
import json
from datetime import datetime, timezone, timedelta
import requests

KST = timezone(timedelta(hours=9))

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")


def _post_webhook(text: str):
    if not SLACK_WEBHOOK_URL:
        return
    requests.post(
        SLACK_WEBHOOK_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps({"text": text}),
        timeout=15,
    )


def _fmt(payload: dict) -> str:
    return (
        f"[KPI]\n"
        f"status={payload.get('status')} | "
        f"total={payload.get('total')} | "
        f"hit={payload.get('hit')} | "
        f"miss={payload.get('miss')} | "
        f"accuracy={payload.get('accuracy')}"
    )


# 🔴 RED 즉시 알림 (외부 사용용)
def send_red_alert(payload: dict):
    _post_webhook(f"🚨 RED ALERT 발생\n{_fmt(payload)}")


# 상태 전이 알림
def notify_status_change(prev_status: str, curr_status: str, payload: dict):
    if prev_status == "YELLOW" and curr_status == "RED":
        _post_webhook(f"⚠️ 상태 전이 (YELLOW → RED)\n{_fmt(payload)}")


# RED 연속 알림
def notify_red_streak(red_streak: int, n: int, payload: dict):
    if payload.get("status") == "RED" and red_streak >= n:
        _post_webhook(f"🚨 RED 연속 {red_streak}회\n{_fmt(payload)}")


# 일일 요약
def send_daily_summary(payload: dict):
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    _post_webhook(f"📌 일일 요약 ({now})\n{_fmt(payload)}")
