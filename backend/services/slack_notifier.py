# backend/services/slack_notifier.py
import os
import json
from datetime import datetime, timezone, timedelta

import requests

KST = timezone(timedelta(hours=9))

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#alerts")


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
        f"[KPI] status={payload.get('status')}  "
        f"total={payload.get('total')}  hit={payload.get('hit')}  "
        f"miss={payload.get('miss')}  acc={payload.get('accuracy')}"
    )


def maybe_notify_status_change(prev_status: str, curr_status: str, payload: dict):
    if prev_status == "YELLOW" and curr_status == "RED":
        _post_webhook(f"⚠️ YELLOW → RED 전이 감지\n{_fmt(payload)}")


def maybe_notify_red_streak(red_streak: int, n: int, payload: dict):
    if n <= 0:
        return
    if payload.get("status") != "RED":
        return
    if red_streak == n:
        _post_webhook(f"🚨 RED 연속 {n}회 도달\n{_fmt(payload)}")


def send_daily_summary(payload: dict):
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    _post_webhook(f"📌 일일 요약 리포트 ({now})\n{_fmt(payload)}")
