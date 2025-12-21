import requests
import os

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")

def notify_slack(message: str):
    if not SLACK_WEBHOOK:
        return
    requests.post(
        SLACK_WEBHOOK,
        json={"text": message},
        timeout=5
    )
