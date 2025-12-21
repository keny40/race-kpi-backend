from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
import os

from backend.routes.season import SEASONS

router = APIRouter()
PDF_DIR = "/tmp/season_reports"
os.makedirs(PDF_DIR, exist_ok=True)

def _make_chart(values: list[float]) -> Drawing:
    d = Drawing(400, 200)
    lp = LinePlot()
    lp.x = 50
    lp.y = 30
    lp.height = 140
    lp.width = 300
    lp.data = [list(enumerate(values))]
    lp.lines[0].strokeColor = colors.blue
    lp.xValueAxis.valueMin = 0
    lp.yValueAxis.valueMin = 0
    lp.yValueAxis.valueMax = 1
    d.add(lp)
    return d

def generate_executive_pdf(period: str, year: int, month=None, quarter=None) -> str:
    name = f"EXEC_{period}_{year}"
    path = f"{PDF_DIR}/{name}.pdf"
    c = canvas.Canvas(path, pagesize=A4)
    w, h = A4
    y = h - 60

    # 제목
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, y, f"Executive Summary ({period.upper()})")
    y -= 40

    # 데이터 집계
    rates = [s["summary"].get("avg_combo_rate_20plus", 0) for s in SEASONS]
    avg_rate = sum(rates) / len(rates) if rates else 0

    c.setFont("Helvetica", 12)
    c.drawString(40, y, f"Overall Avg Hit Rate (20+): {avg_rate:.2%}")
    y -= 30

    # 차트
    chart = _make_chart(rates[-20:])
    chart.drawOn(c, 40, y - 180)
    y -= 200

    c.setFont("Helvetica", 10)
    c.drawString(40, y, "• 안정성 추세: 최근 시즌 기준 평균 적중률 변화")
    y -= 20
    c.drawString(40, y, "• 운영 상태: 자동 LOCK / 자동 프리셋 / 자동 리포트 활성")
    y -= 40

    c.setFont("Helvetica-Oblique", 9)
    c.drawString(40, y, f"Generated UTC: {datetime.utcnow().isoformat()}")

    c.showPage()
    c.save()
    return path
