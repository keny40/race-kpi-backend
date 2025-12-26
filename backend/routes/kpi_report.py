# backend/routes/kpi_report.py

from fastapi import APIRouter
from fastapi.responses import FileResponse
import sqlite3
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

DB_PATH = os.getenv("DB_PATH", "races.db")

router = APIRouter(prefix="/api/kpi/report", tags=["kpi-report"])


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def build_kpi_pdf(path: str, executive: bool = False):
    conn = _conn()
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT
            race_id,
            decision,
            winner,
            confidence,
            result
        FROM v_race_match
        ORDER BY race_id
    """).fetchall()

    total = len(rows)
    hit = sum(1 for r in rows if r["result"] == "HIT")
    miss = sum(1 for r in rows if r["result"] == "MISS")
    pass_cnt = sum(1 for r in rows if r["result"] == "PASS")

    accuracy = round(hit / (hit + miss), 3) if (hit + miss) > 0 else 0

    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "Race KPI Report" + (" (Executive)" if executive else ""))
    y -= 40

    c.setFont("Helvetica", 11)
    c.drawString(40, y, f"Total predictions: {total}")
    y -= 20
    c.drawString(40, y, f"HIT: {hit}")
    y -= 20
    c.drawString(40, y, f"MISS: {miss}")
    y -= 20
    c.drawString(40, y, f"PASS: {pass_cnt}")
    y -= 20
    c.drawString(40, y, f"Accuracy: {accuracy}")
    y -= 40

    if not executive:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Details")
        y -= 20
        c.setFont("Helvetica", 10)

        for r in rows:
            line = (
                f"{r['race_id']} | "
                f"decision={r['decision']} | "
                f"winner={r['winner']} | "
                f"conf={r['confidence']} | "
                f"result={r['result']}"
            )
            c.drawString(40, y, line)
            y -= 14
            if y < 50:
                c.showPage()
                y = height - 50
                c.setFont("Helvetica", 10)

    c.showPage()
    c.save()
    conn.close()


@router.post("/pdf")
def report_pdf():
    filename = f"kpi_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    path = os.path.join("/tmp", filename)

    build_kpi_pdf(path, executive=False)

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=filename
    )


@router.post("/executive")
def executive_pdf():
    filename = f"executive_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    path = os.path.join("/tmp", filename)

    build_kpi_pdf(path, executive=True)

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=filename
    )
