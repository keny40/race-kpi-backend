import os
from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

from backend.services.red_score import explain_score, get_recent_statuses


def _try_make_chart_png(points):
    """
    points: [{"t": "...", "score": float}, ...]
    matplotlib 없으면 None 반환
    """
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return None

    xs = list(range(len(points)))
    ys = [p["score"] for p in points]

    buf = BytesIO()
    plt.figure()
    plt.plot(xs, ys)
    plt.title("RED Score Trend")
    plt.xlabel("Index (old -> new)")
    plt.ylabel("Score")
    plt.tight_layout()
    plt.savefig(buf, format="png", dpi=140)
    plt.close()
    buf.seek(0)
    return buf


def build_red_report_pdf(output_path: str | None = None) -> str:
    """
    1페이지 운영 리포트:
    - 현재 RED score / threshold / locked
    - 최근 상태 로그(요약)
    - 점수 추이(가능하면 차트 이미지)
    """
    now = datetime.utcnow()
    exp = explain_score()
    recent = get_recent_statuses(limit=60)

    # 간단 추이: terms 누적합을 시간순으로 쌓아 score curve처럼 표시
    running = 0.0
    points = []
    for term in exp["terms"]:
        running += term["add"]
        points.append({"t": term["created_at"], "score": round(running, 4)})

    chart_png = _try_make_chart_png(points)

    if output_path is None:
        os.makedirs("tmp", exist_ok=True)
        output_path = f"tmp/red_report_{now.strftime('%Y%m%d_%H%M%S')}.pdf"

    c = canvas.Canvas(output_path, pagesize=A4)
    w, h = A4

    y = h - 20 * mm
    c.setFont("Helvetica-Bold", 15)
    c.drawString(20 * mm, y, "RED Operational Report")
    y -= 8 * mm

    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y, f"Generated (UTC): {now.isoformat(timespec='seconds')}")
    y -= 10 * mm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, "1) Current Score")
    y -= 7 * mm

    c.setFont("Helvetica", 11)
    c.drawString(22 * mm, y, f"Score: {exp['score']}    Threshold: {exp['threshold']}    Locked: {exp['locked']}")
    y -= 10 * mm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, "2) Recent Status (last 12~60 logs)")
    y -= 7 * mm

    c.setFont("Helvetica", 9)
    # 최근 20개만 인쇄
    tail = recent[-20:]
    for r in tail[::-1]:
        c.drawString(22 * mm, y, f"{r['created_at']}  -  {r['status']}")
        y -= 4.5 * mm
        if y < 70 * mm:
            break

    # 차트 영역
    y_chart_top = 65 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y_chart_top, "3) Score Trend")
    y_img = y_chart_top - 6 * mm

    if chart_png is not None:
        # reportlab 이미지 드로잉
        from reportlab.lib.utils import ImageReader
        img = ImageReader(chart_png)
        c.drawImage(img, 20 * mm, 15 * mm, width=(w - 40 * mm), height=(y_img - 15 * mm), preserveAspectRatio=True, anchor='sw')
    else:
        c.setFont("Helvetica", 10)
        c.drawString(22 * mm, y_img, "Chart unavailable (matplotlib not installed). Showing numeric summary only.")
        y_img -= 7 * mm
        c.setFont("Helvetica", 9)
        for p in points[-10:]:
            c.drawString(22 * mm, y_img, f"{p['t']}  score={p['score']}")
            y_img -= 4.5 * mm
            if y_img < 20 * mm:
                break

    c.showPage()
    c.save()
    return output_path
