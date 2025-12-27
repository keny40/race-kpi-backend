# backend/services/red_alert.py

import os
from datetime import datetime
from backend.routes.kpi_report import build_kpi_pdf
from backend.services.slack_alert import send_pdf_to_slack


def send_red_alert_with_pdf(reason: str):
    """
    RED 상태 발생 시
    - KPI PDF 생성
    - Slack에 PDF 업로드
    """

    filename = f"RED_KPI_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = os.path.join("/tmp", filename)

    # PDF 생성
    build_kpi_pdf(pdf_path, executive=True)

    # Slack 전송
    send_pdf_to_slack(
        pdf_path=pdf_path,
        title="🚨 RED 상태 KPI 리포트",
        message=f"*RED ALERT 발생*\n사유: {reason}"
    )
