from pathlib import Path
from datetime import datetime
import json


BASE_DIR = Path(__file__).resolve().parent.parent.parent
PDF_DIR = BASE_DIR / "generated"
PDF_DIR.mkdir(exist_ok=True)


def generate_admin_log_pdf(logs: list[dict]) -> str:
    """
    관리자 액션 로그 PDF 생성
    현재는 임시 구현 (JSON → TXT 형태)
    추후 reportlab / weasyprint 등으로 교체 가능
    """
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_path = PDF_DIR / f"admin_logs_{ts}.txt"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("ADMIN ACTION LOGS\n")
        f.write("=" * 40 + "\n\n")
        for row in logs:
            f.write(json.dumps(row, ensure_ascii=False))
            f.write("\n")

    return str(file_path)
