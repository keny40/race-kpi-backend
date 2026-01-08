# backend/services/slack_notifier.py

import os
import json
import urllib.request
import time

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")


def send_slack(text: str, level: str = "info", extra: dict | None = None):
    if not SLACK_WEBHOOK_URL:
        return {"ok": False, "reason": "no_webhook"}

    color = {
        "info": "#36a64f",
        "warn": "#ffae42",
        "error": "#ff4d4d",
    }.get(level, "#cccccc")

    payload = {
        "attachments": [
            {
                "color": color,
                "text": text,
                "footer": f"Race System · {int(time.time())}",
            }
        ]
    }

    if extra:
        payload["attachments"][0]["fields"] = [
            {"title": k, "value": json.dumps(v, ensure_ascii=False), "short": False}
            for k, v in extra.items()
        ]

    req = urllib.request.Request(
        SLACK_WEBHOOK_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(req, timeout=5) as resp:
        return {"ok": resp.status == 200}
