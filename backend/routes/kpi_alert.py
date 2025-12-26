# backend/routes/kpi_alert.py

from fastapi import APIRouter
from backend.routes.kpi_status import get_kpi_status
from backend.routes.kpi_report import build_kpi_pdf
from backend.services.slack_client import send_slack_message
from datetime import datetime
import os

router = APIRouter(prefix="/api/kpi/alert", tags=["kpi-alert"])


@router.post("/check")
def check_and_alert():
    status = get_kpi_status()

    if status["status"] != "RED":
        return {"alert": "skip", "status": status["status"]}

    filename = f"kpi_red_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    path = os.path.join("/tmp", filename)

    build_kpi_pdf(path, executive=True)

    send_slack_message(
        text=(
            "🚨 *KPI STATUS: RED*\n"
            f"- Total: {status['total']}\n"
            f"- HIT: {status['hit']}\n"
            f"- MISS: {status['miss']}\n"
            f"- Accuracy: {status['accuracy']}"
        ),
        attachments=[
            {
                "title": "Executive KPI PDF",
                "text": f"파일 생성됨: {filename}"
            }
        ]
    )

    return {"alert": "sent", "file": filename}
