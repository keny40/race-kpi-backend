# backend/pdf_reports.py
from __future__ import annotations

from typing import Dict, Any
from io import BytesIO

def build_ops_pdf_bytes(
    title: str,
    period_label: str,
    time_min: str,
    time_max: str,
    summary: Dict[str, Any],
) -> bytes:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
    except Exception as e:
        # reportlab 미설치면 여기서 바로 원인 노출
        raise RuntimeError("reportlab is required. run: pip install reportlab") from e

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=14*mm, rightMargin=14*mm, topMargin=14*mm, bottomMargin=14*mm)

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"<b>{title}</b>", styles["Title"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(f"Period: <b>{period_label}</b>", styles["Normal"]))
    story.append(Paragraph(f"Range: {time_min} ~ {time_max}", styles["Normal"]))
    story.append(Spacer(1, 10))

    data = [
        ["Metric", "Value"],
        ["Total predictions", str(summary.get("total", 0))],
        ["PASS", f"{summary.get('pass', 0)}  (rate {summary.get('pass_rate', 0.0):.2%})"],
        ["Non-PASS", str(summary.get("non_pass", 0))],
        ["HIT (if available)", str(summary.get("hit", 0))],
        ["MISS (if available)", str(summary.get("miss", 0))],
        ["Hit rate excl. PASS", f"{summary.get('hit_rate_ex_pass', 0.0):.2%}"],
    ]

    tbl = Table(data, colWidths=[60*mm, 110*mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.black),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Notes:", styles["Heading3"]))
    story.append(Paragraph("- PASS rate is computed from predictions.label='PASS'", styles["Normal"]))
    story.append(Paragraph("- HIT/MISS are shown only if a feedback/results table exists with is_hit + created_at", styles["Normal"]))

    doc.build(story)
    return buf.getvalue()
