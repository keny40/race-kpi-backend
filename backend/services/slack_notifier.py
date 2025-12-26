# backend/services/slack_notifier.py

import os
import requests

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def send_slack_file(text: str, file_path: str):
    if not SLACK_WEBHOOK_URL:
        return

    with open(file_path, "rb") as f:
        requests.post(
            SLACK_WEBHOOK_URL,
            data={"text": text},
            files={"file": f}
        )
