# backend/services/slack_client.py

import os
import json
import requests

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def send_slack_message(text: str, attachments: list | None = None):
    if not SLACK_WEBHOOK_URL:
        return

    payload = {
        "text": text
    }

    if attachments:
        payload["attachments"] = attachments

    requests.post(
        SLACK_WEBHOOK_URL,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
        timeout=5
    )
