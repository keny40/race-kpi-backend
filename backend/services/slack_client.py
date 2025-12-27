import os
import requests

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")  # xoxb-****
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL")     # 예: C07XXXXXXX


def upload_pdf_to_slack(pdf_path: str, title: str, initial_comment: str):
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL:
        raise RuntimeError("Slack token or channel not configured")

    url = "https://slack.com/api/files.upload"

    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
    }

    with open(pdf_path, "rb") as f:
        files = {
            "file": f
        }
        data = {
            "channels": SLACK_CHANNEL,
            "title": title,
            "initial_comment": initial_comment
        }

        resp = requests.post(url, headers=headers, files=files, data=data)
        result = resp.json()

    if not result.get("ok"):
        raise RuntimeError(f"Slack upload failed: {result}")

    return result
