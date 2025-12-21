from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
from services.kpi import calc_kpi

def generate_kpi_pdf(path="kpi_report.pdf", mode="weight"):
    kpi = calc_kpi(mode=mode)

    c = canvas.Canvas(path, pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, "KRA Race KPI Report")

    c.setFont("Helvetica", 12)
    y = 760
    for k, v in kpi.items():
        c.drawString(50, y, f"{k}: {v}")
        y -= 22

    c.drawString(50, 80, f"Generated at {datetime.now().isoformat(timespec='seconds')}")
    c.save()
