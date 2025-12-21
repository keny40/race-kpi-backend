import os
import uuid
from typing import Dict, Any
from statistics import mean

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

from backend import storage


def _reports_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    d = os.path.join(here, "reports")
    os.makedirs(d, exist_ok=True)
    return d


def build_executive_summary_pdf(year: int, month: int) -> Dict[str, Any]:
    report_id = str(uuid.uuid4())
    path = os.path.join(_reports_dir(), f"exec_{year:04d}-{month:02d}_{report_id}.pdf")

    preds = storage.list_predictions_for_month(year, month)
    results = storage.list_results_for_month(year, month)

    hits = sum(1 for r in results if r["outcome"] == "HIT")
    misses = sum(1 for r in results if r["outcome"] == "MISS")
    passes = sum(1 for r in results if r["outcome"] == "PASS")
    total = hits + misses
    accuracy = round(hits / total, 4) if total > 0 else 0.0

    confidences = [p["confidence"] for p in preds if p.get("confidence") is not None]
    avg_conf = round(mean(confidences), 4) if confidences else 0.0

    # 간단 인사이트
    if accuracy >= 0.55 and avg_conf >= 0.35:
        insight = "예측 안정 구간"
    elif accuracy < 0.45 or passes / max(1, len(results)) > 0.3:
        insight = "위험 구간 진입"
    else:
        insight = "변동성 증가 구간"

    c = canvas.Canvas(path, pagesize=A4)
    w, h = A4

    c.setFont("Helvetica-Bold", 18)
    c.drawString(20 * mm, h - 20 * mm, "Horse Race Predictor – Executive Summary")

    c.setFont("Helvetica", 12)
    c.drawString(20 * mm, h - 30 * mm, f"Period: {year:04d}-{month:02d}")

    y = h - 50 * mm
    c.setFont("Helvetica-Bold", 13)
    c.drawString(20 * mm, y, "Key Metrics")
    y -= 10 * mm

    c.setFont("Helvetica", 12)
    c.drawString(25 * mm, y, f"Accuracy        : {accuracy:.4f}")
    y -= 8 * mm
    c.drawString(25 * mm, y, f"Hits / Misses   : {hits} / {misses}")
    y -= 8 * mm
    c.drawString(25 * mm, y, f"Passes          : {passes}")
    y -= 8 * mm
    c.drawString(25 * mm, y, f"Avg Confidence  : {avg_conf:.4f}")

    y -= 15 * mm
    c.setFont("Helvetica-Bold", 13)
    c.drawString(20 * mm, y, "System Insight")
    y -= 10 * mm

    c.setFont("Helvetica", 12)
    c.drawString(25 * mm, y, insight)

    c.save()

    storage.insert_report(
        report_id=report_id,
        kind="executive",
        file_path=path,
        season_key=None,
        year=year,
        month=month,
    )

    return {
        "report_id": report_id,
        "file_path": path,
        "kind": "executive",
        "year": year,
        "month": month,
        "accuracy": accuracy,
        "avg_confidence": avg_conf,
        "insight": insight,
    }
