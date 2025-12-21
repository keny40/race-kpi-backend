from fastapi import APIRouter
import requests
import os

router = APIRouter()

NOTIFY = {
    "slack_bot_token": "",   # xoxb- 로 시작하는 Bot Token
    "slack_channel": "",     # 채널 ID (예: C01ABCDEF)
}

def upload_pdf_to_slack(filepath: str, title: str):
    if not NOTIFY["slack_bot_token"]:
        return

    with open(filepath, "rb") as f:
        requests.post(
            "https://slack.com/api/files.upload",
            headers={
                "Authorization": f"Bearer {NOTIFY['slack_bot_token']}"
            },
            data={
                "channels": NOTIFY["slack_channel"],
                "title": title
            },
            files={"file": f}
        )
