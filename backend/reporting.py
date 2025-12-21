# backend/reporting.py
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from .storage import fetch_kpi_summary


def build_kpi_pdf(days: int = 30) -> bytes:
    kpi = fetch_kpi_summary(days)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, 780, "KPI Summary Report")

    c.setFont("Helvetica", 12)
    c.drawString(72, 740, f"Period: Last {days} days")

    c.drawString(72, 700, f"ROI: {kpi['roi'] * 100:.2f}%")
    c.drawString(72, 675, f"Hit Rate: {kpi['hit_rate'] * 100:.2f}%")
    c.drawString(72, 650, f"PASS Rate: {kpi['pass_rate'] * 100:.2f}%")

    c.showPage()
    c.save()

    pdf = buffer.getvalue()
    buffer.close()
    return pdf
