# backend/mailer.py
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import Optional


def send_email_with_attachment(
    to_email: str,
    subject: str,
    body: str,
    attachment_path: Optional[str] = None,
) -> None:
    """
    환경변수 필요:
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM
    """
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    pw = os.getenv("SMTP_PASS")
    from_email = os.getenv("SMTP_FROM", user)

    if not host or not user or not pw or not from_email:
        raise RuntimeError("SMTP env not set: SMTP_HOST/SMTP_USER/SMTP_PASS/SMTP_FROM")

    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    if attachment_path:
        with open(attachment_path, "rb") as f:
            data = f.read()
        filename = os.path.basename(attachment_path)
        msg.add_attachment(data, maintype="application", subtype="pdf", filename=filename)

    with smtplib.SMTP(host, port) as s:
        s.starttls()
        s.login(user, pw)
        s.send_message(msg)
