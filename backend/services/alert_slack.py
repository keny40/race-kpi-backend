# backend/services/alert_slack.py
import os
import json
import time
import requests
from typing import Dict, Any

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
COOLDOWN_SEC = 900  # 동일 경보 쿨다운 15분
_last_sent = {}

def _can_send(key: str) -> bool:
    now = time.time()
    last = _last_sent.get(key, 0)
    if now - last < COOLDOWN_SEC:
        return False
    _last_sent[key] = now
    return True

def send(text: str, blocks: list | None = None):
    if not SLACK_WEBHOOK_URL:
        return
    payload = {"text": text}
    if blocks:
        payload["blocks"] = blocks
    requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)

def alert_strategy_drop(strategy: str, hit_rate: float, avg_roi: float):
    key = f"drop:{strategy}"
    if not _can_send(key):
        return
    send(
        f"🚨 *Strategy Drop* `{strategy}`\n• hit_rate={hit_rate:.3f}\n• avg_roi={avg_roi:.3f}",
        blocks=[
            {"type":"section","text":{"type":"mrkdwn",
             "text":f"*Strategy Drop*\n`{strategy}`\n• hit_rate *{hit_rate:.3f}*\n• avg_roi *{avg_roi:.3f}*"}}
        ]
    )

def daily_summary(summary: list[Dict[str, Any]], run_mode: str):
    key = "daily"
    if not _can_send(key):
        return
    lines = "\n".join(
        [f"• `{s['strategy']}` hit={s['hit_rate']:.3f} roi={s['avg_roi']:.3f} n={s['count']}"
         for s in summary]
    )
    send(
        f"📊 *Daily KPI Summary* ({run_mode})\n{lines}",
        blocks=[
            {"type":"section","text":{"type":"mrkdwn",
             "text":f"*Daily KPI Summary* ({run_mode})\n{lines}"}}
        ]
    )
