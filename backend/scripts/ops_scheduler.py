# backend/scripts/ops_scheduler.py
from __future__ import annotations

import argparse
from datetime import date

from backend.pdf_reports import build_ops_pdf
from backend.mailer import send_email_with_attachment


def run(period: str, email: str | None):
    pdf_path = build_ops_pdf(period=period, end_day=date.today())
    print(f"[OK] PDF generated: {pdf_path}")

    if email:
        send_email_with_attachment(
            to_email=email,
            subject=f"OPS Report ({period})",
            body=f"Attached: {pdf_path}",
            attachment_path=pdf_path,
        )
        print(f"[OK] Email sent: {email}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--period", default="monthly", choices=["daily", "monthly", "quarterly"])
    p.add_argument("--email", default=None, help="recipient email (optional)")
    args = p.parse_args()
    run(args.period, args.email)


if __name__ == "__main__":
    main()
