# backend/services/slack_alert.py

import os
import requests

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")  # xoxb-***
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")  # Cxxxxxx


def send_pdf_to_slack(pdf_path: str, title: str, message: str):
    """
    Slack 채널에 PDF 파일 업로드 + 메시지 전송
    """

    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL_ID:
        print("[Slack] Token or Channel ID missing")
        return

    url = "https://slack.com/api/files.upload"

    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
    }

    data = {
        "channels": SLACK_CHANNEL_ID,
        "initial_comment": message,
        "title": title
    }

    with open(pdf_path, "rb") as f:
        files = {
            "file": f
        }

        response = requests.post(
            url,
            headers=headers,
            data=data,
            files=files,
            timeout=10
        )

    result = response.json()

    if not result.get("ok"):
        print("[Slack] Upload failed:", result)
    else:
        print("[Slack] PDF uploaded successfully")
