# backend/services/slack_client.py
import os
import requests
from typing import Optional


class SlackClient:
    def __init__(self):
        self.token = os.getenv("SLACK_BOT_TOKEN", "").strip()
        self.channel = os.getenv("SLACK_CHANNEL_ID", "").strip()

    def _check_ready(self):
        if not self.token:
            raise RuntimeError("Missing env SLACK_BOT_TOKEN")
        if not self.channel:
            raise RuntimeError("Missing env SLACK_CHANNEL_ID")

    def post_message(self, text: str) -> dict:
        self._check_ready()
        url = "https://slack.com/api/chat.postMessage"
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json; charset=utf-8"}
        payload = {"channel": self.channel, "text": text}
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        data = r.json()
        if not data.get("ok"):
            raise RuntimeError(f"Slack postMessage failed: {data}")
        return data

    def upload_file(self, filename: str, file_bytes: bytes, initial_comment: Optional[str] = None) -> dict:
        self._check_ready()
        url = "https://slack.com/api/files.upload"
        headers = {"Authorization": f"Bearer {self.token}"}
        data = {"channels": self.channel}
        if initial_comment:
            data["initial_comment"] = initial_comment

        files = {"file": (filename, file_bytes, "application/pdf")}
        r = requests.post(url, headers=headers, data=data, files=files, timeout=30)
        data = r.json()
        if not data.get("ok"):
            raise RuntimeError(f"Slack files.upload failed: {data}")
        return data
