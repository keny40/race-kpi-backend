# backend/routes/admin_pre_race_export_pdf.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import io
from backend.services.db import get_conn

router = APIRouter(prefix="/api/admin/pre-race", tags=["admin-pre-race-export"])

@router.get("/report/pdf")
def export_pdf():
    conn = get_conn()
    rows = conn.execute("""
      SELECT race_id, run_at, confidence, decision
      FROM pre_race_run_history
      ORDER BY run_at DESC LIMIT 50
    """).fetchall()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf)
    styles = getSampleStyleSheet()
    story = [Paragraph("Pre-Race Report", styles["Title"])]

    for r in rows:
        story.append(Paragraph(
          f'{r["race_id"]} | {r["run_at"]} | conf={r["confidence"]} | {r["decision"]}',
          styles["Normal"]
        ))

    doc.build(story)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf")
