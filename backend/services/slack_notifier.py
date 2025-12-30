import os
import requests
import json
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

def _post(text: str):
    if not SLACK_WEBHOOK_URL:
        return
    try:
        requests.post(
            SLACK_WEBHOOK_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps({"text": text}),
            timeout=5,
        )
    except Exception:
        # Slack 실패로 서버 죽지 않게
        pass

def _fmt(payload: dict) -> str:
    # payload가 없거나 일부 키가 없어도 안전
    return (
        f"status={payload.get('status')}  "
        f"total={payload.get('total')}  hit={payload.get('hit')}  "
        f"miss={payload.get('miss')}  acc={payload.get('accuracy')}"
    )

# === NEW “official” APIs ===
def send_admin_action(action: str, detail: str = ""):
    _post(f"[ADMIN ACTION]\n• action: {action}\n• detail: {detail}")

def send_red_alert(reason: str, score: float | None = None):
    msg = f"[RED ALERT]\n• reason: {reason}"
    if score is not None:
        msg += f"\n• score: {score}"
    _post(msg)

def notify_status_change(prev_status: str, new_status: str, reason: str | None = None):
    msg = f"[STATUS CHANGE]\n• from: {prev_status}\n• to: {new_status}"
    if reason:
        msg += f"\n• reason: {reason}"
    _post(msg)

def notify_red_streak(count: int, threshold: int, action: str | None = None):
    msg = f"[RED STREAK]\n• count: {count}\n• threshold: {threshold}"
    if action:
        msg += f"\n• action: {action}"
    _post(msg)

def send_daily_summary(payload: dict):
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    _post(f"[DAILY SUMMARY] {now}\n{_fmt(payload)}")

# === BACKWARD COMPAT aliases (기존 코드 import 깨짐 방지) ===
def _post_webhook(text: str):
    _post(text)

def maybe_notify_status_change(prev_status: str, curr_status: str, payload: dict):
    # 기존 구현 호환
    if prev_status == "YELLOW" and curr_status == "RED":
        _post(f"⚠️ YELLOW → RED\n{_fmt(payload)}")

def maybe_notify_red_streak(red_streak: int, n: int, payload: dict):
    if n <= 0:
        return
    if payload.get("status") != "RED":
        return
    if red_streak == n:
        _post(f"🚨 RED streak {n}\n{_fmt(payload)}")
