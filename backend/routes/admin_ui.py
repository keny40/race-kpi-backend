# backend/routes/admin_ui.py
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pathlib import Path

router = APIRouter(tags=["admin-ui"])

BASE_DIR = Path(__file__).resolve().parents[1]  # backend/
STATIC_DIR = BASE_DIR / "static"
ADMIN_HTML = STATIC_DIR / "admin.html"


@router.get("/admin", response_class=HTMLResponse)
def admin_page():
    if ADMIN_HTML.exists():
        return ADMIN_HTML.read_text(encoding="utf-8")
    return HTMLResponse(
        "<h3>admin.html not found</h3><p>backend/static/admin.html 파일이 필요합니다.</p>",
        status_code=500,
    )
