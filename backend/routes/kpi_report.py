import io
import sqlite3
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "races.db")


def generate_kpi_report_pdf_bytes(
    *,
    period: str,
    summary_pages: int,
    include_chart: bool = False
) -> bytes:
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("""
        SELECT substr(created_at,1,7),
               SUM(CASE WHEN decision=winner THEN 1 ELSE 0 END),
               COUNT(*)
        FROM predictions p
        LEFT JOIN results r ON p.race_id=r.race_id
        GROUP BY substr(created_at,1,7)
        ORDER BY 1
    """)
    rows = cur.fetchall()
    con.close()

    labels = [r[0] for r in rows]
    values = [
        round((r[1] or 0) / max(1, r[2]) * 100, 2)
        for r in rows
    ]

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    c.setFont("Helvetica-Bold", 18)
    c.drawString(2*cm, h-2*cm, "KPI REPORT")
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, h-3*cm, f"Generated: {datetime.now()}")

    if include_chart and values:
        drawing = Drawing(400, 200)
        chart = HorizontalLineChart()
        chart.x = 50
        chart.y = 50
        chart.width = 300
        chart.height = 120
        chart.data = [values]
        chart.categoryAxis.categoryNames = labels
        chart.valueAxis.valueMin = 0
        chart.valueAxis.valueMax = 100
        chart.valueAxis.valueStep = 20
        drawing.add(chart)
        drawing.drawOn(c, 2*cm, h-10*cm)

    c.showPage()
    c.save()
    return buf.getvalue()
