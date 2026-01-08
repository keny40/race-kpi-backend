# backend/routes/collect_settings.py
from fastapi import APIRouter, Request, HTTPException
import os

from backend.services.settings_store import get_all, set_setting, ensure_tables

router = APIRouter(prefix="/api/collect", tags=["collect-settings"])

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

def _auth(request: Request):
    token = request.headers.get("x-admin-token", "")
    if not ADMIN_PASSWORD or token != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="unauthorized")

@router.get("/settings")
def read_settings(request: Request):
    _auth(request)
    ensure_tables()
    return {"ok": True, "settings": get_all()}

@router.post("/settings")
async def update_settings(request: Request):
    _auth(request)
    body = await request.json()
    # expected keys:
    # AUTO_PRERACE_IMMEDIATE: "0"/"1"
    # AUTO_PRERACE_BEFORE_MIN: "10"
    for k, v in body.items():
        if k in ("AUTO_PRERACE_IMMEDIATE", "AUTO_PRERACE_BEFORE_MIN"):
            set_setting(k, str(v))
    return {"ok": True, "settings": get_all()}
