import os
import json
import requests
from typing import Optional

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def send_slack_message(
    text: str,
    blocks: Optional[list] = None
):
    """
    Slack Incoming Webhook으로 메시지 전송

    text   : 기본 텍스트
    blocks : Slack Block Kit (선택)
    """

    if not SLACK_WEBHOOK_URL:
        # Slack 설정 없어도 서버는 죽지 않게
        print("[WARN] SLACK_WEBHOOK_URL not set")
        return

    payload = {"text": text}
    if blocks:
        payload["blocks"] = blocks

    res = requests.post(
        SLACK_WEBHOOK_URL,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
        timeout=5
    )

    res.raise_for_status()
