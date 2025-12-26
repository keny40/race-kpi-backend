# backend/services/pdf_generator.py

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_kpi_pdf(reason: str) -> str:
    filename = f"kpi_auto_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    path = os.path.join("/tmp", filename)

    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, height - 50, "KPI AUTO REPORT")

    c.setFont("Helvetica", 12)
    c.drawString(40, height - 100, f"Generated at: {datetime.utcnow().isoformat()}")
    c.drawString(40, height - 130, f"Reason: {reason}")
    c.drawString(40, height - 160, "Action: Prediction FORCED PASS")

    c.showPage()
    c.save()

    return path
