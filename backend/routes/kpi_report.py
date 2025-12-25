from fastapi import APIRouter
from fastapi.responses import FileResponse
from datetime import datetime
import os

from backend.db.conn import get_conn

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

router = APIRouter(
    prefix="/api/kpi",
    tags=["kpi-report"]
)

REPORT_DIR = "reports"
os.makedirs(REPORT_DIR, exist_ok=True)


def build_kpi_pdf(path: str):
    con = get_conn()
    cur = con.cursor()

    cur.execute("""
        SELECT
            COUNT(*) AS total,
            COALESCE(SUM(result = 'HIT'), 0) AS hit,
            COALESCE(SUM(result = 'MISS'), 0) AS miss
        FROM v_race_match
    """)
    total, hit, miss = cur.fetchone()
    con.close()

    hit = hit or 0
    miss = miss or 0

    denom = hit + miss
    accuracy = round(hit / denom, 4) if denom > 0 else 0.0

    if accuracy >= 0.6:
        status = "OK"
    elif accuracy >= 0.45:
        status = "WARN"
    else:
        status = "FAIL"

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(path, pagesize=A4)

    story = []
    story.append(Paragraph("Executive KPI Summary", styles["Title"]))
    story.append(Spacer(1, 16))

    table = Table([
        ["Total", total],
        ["HIT", hit],
        ["MISS", miss],
        ["Accuracy", accuracy],
        ["Status", status],
    ])

    story.append(table)
    doc.build(story)


@router.post("/report/pdf")
def report_pdf():
    filename = f"kpi_{datetime.now():%Y%m%d_%H%M%S}.pdf"
    path = os.path.join(REPORT_DIR, filename)
    build_kpi_pdf(path)
    return FileResponse(path, filename=filename, media_type="application/pdf")


@router.post("/report/executive")
def executive_pdf():
    filename = f"exec_{datetime.now():%Y%m%d}.pdf"
    path = os.path.join(REPORT_DIR, filename)
    build_kpi_pdf(path)
    return FileResponse(path, filename=filename, media_type="application/pdf")
