import os
import requests

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#general")

SLACK_FILE_UPLOAD_URL = "https://slack.com/api/files.upload"


def upload_pdf_to_slack(
    pdf_path: str,
    title: str,
    message: str
):
    """
    PDF 파일을 Slack 채널에 업로드 (Bot Token 방식)
    """

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
    }

    data = {
        "channels": SLACK_CHANNEL,
        "initial_comment": message,
        "title": title
    }

    with open(pdf_path, "rb") as f:
        files = {
            "file": (os.path.basename(pdf_path), f, "application/pdf")
        }

        resp = requests.post(
            SLACK_FILE_UPLOAD_URL,
            headers=headers,
            data=data,
            files=files,
            timeout=15
        )

    result = resp.json()

    if not result.get("ok"):
        raise RuntimeError(
            f"Slack upload failed: {result}"
        )

    return result
