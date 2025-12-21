import os
import smtplib
from email.message import EmailMessage
from typing import Optional

from backend.retry_queue import enqueue


# =========================
# Slack
# =========================
def send_slack(webhook_url: str, text: str) -> None:
    if not webhook_url:
        return
    try:
        import requests
        requests.post(webhook_url, json={"text": text}, timeout=5)
    except Exception as e:
        enqueue("slack", {"text": text}, str(e))


# =========================
# Email
# =========================
def send_email(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_pass: str,
    to_addr: str,
    subject: str,
    body: str,
    attach_path: Optional[str] = None,
) -> None:
    if not (smtp_host and smtp_user and smtp_pass and to_addr):
        return

    msg = EmailMessage()
    msg["From"] = smtp_user
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)

    if attach_path and os.path.exists(attach_path):
        with open(attach_path, "rb") as f:
            data = f.read()
        msg.add_attachment(
            data,
            maintype="application",
            subtype="pdf",
            filename=os.path.basename(attach_path),
        )

    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as s:
            s.login(smtp_user, smtp_pass)
            s.send_message(msg)
    except Exception as e:
        enqueue(
            "email",
            {
                "to": to_addr,
                "subject": subject,
                "attach_path": attach_path,
            },
            str(e),
        )
