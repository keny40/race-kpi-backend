from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[2]  # .../backend/services -> .../
OUT_DIR = BASE_DIR / "generated"
OUT_DIR.mkdir(exist_ok=True)

def generate_admin_log_pdf(logs: list[dict]) -> str:
    """
    1) reportlab 설치되어 있으면 진짜 PDF 생성
    2) 없으면 '최소 PDF' 형태로 텍스트를 박아넣은 PDF 생성(깨지지 않게)
    """
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = OUT_DIR / f"admin_logs_{ts}.pdf"

    # 1) reportlab 우선
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(str(path), pagesize=A4)
        width, height = A4

        y = height - 50
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, y, "ADMIN ACTION LOGS")
        y -= 20

        c.setFont("Helvetica", 9)
        for r in logs:
            line = f"{r.get('created_at','')} | {r.get('action','')} | {r.get('detail','')}"
            if y < 60:
                c.showPage()
                y = height - 50
                c.setFont("Helvetica", 9)
            c.drawString(40, y, line[:140])
            y -= 12

        c.save()
        return str(path)

    except Exception:
        pass

    # 2) 최소 PDF fallback (외부 의존성 없이)
    text_lines = ["ADMIN ACTION LOGS"] + [
        f"{r.get('created_at','')} | {r.get('action','')} | {r.get('detail','')}"
        for r in logs
    ]
    text = "\n".join(text_lines).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 10 Tf 50 780 Td ({text[:2000]}) Tj ET"  # 너무 길면 깨질 수 있어 제한

    # 아주 단순한 PDF 구조
    pdf = (
        "%PDF-1.4\n"
        "1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n"
        "2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n"
        "3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        "/Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj\n"
        f"4 0 obj<< /Length {len(stream)} >>stream\n{stream}\nendstream endobj\n"
        "5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n"
        "xref\n0 6\n0000000000 65535 f \n"
        "trailer<< /Size 6 /Root 1 0 R >>\nstartxref\n0\n%%EOF\n"
    )

    path.write_text(pdf, encoding="latin-1", errors="ignore")
    return str(path)
