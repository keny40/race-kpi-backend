import os
import smtplib
from email.message import EmailMessage
import requests

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL")

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
MAIL_TO = os.getenv("MAIL_TO")
MAIL_FROM = os.getenv("MAIL_FROM", SMTP_USER)

def send_slack_text(text: str):
    if not SLACK_WEBHOOK_URL:
        return
    try:
        requests.post(SLACK_WEBHOOK_URL, json={"text": text}, timeout=10)
    except Exception:
        pass

def send_slack_file(text: str, pdf_path: str):
    if not (SLACK_BOT_TOKEN and SLACK_CHANNEL):
        return
    try:
        headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
        with open(pdf_path, "rb") as f:
            files = {"file": f}
            data = {
                "channels": SLACK_CHANNEL,
                "initial_comment": text,
                "filename": os.path.basename(pdf_path),
                "title": os.path.basename(pdf_path),
            }
            requests.post(
                "https://slack.com/api/files.upload",
                headers=headers,
                files=files,
                data=data,
                timeout=30
            )
    except Exception:
        pass

def send_mail(subject: str, body: str, attachment_path: str | None = None):
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS and MAIL_TO):
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = MAIL_FROM
    msg["To"] = MAIL_TO
    msg.set_content(body)

    if attachment_path:
        with open(attachment_path, "rb") as f:
            data = f.read()
        msg.add_attachment(
            data,
            maintype="application",
            subtype="pdf",
            filename=os.path.basename(attachment_path),
        )

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
    except Exception:
        pass
