# backend/routes/admin_import.py
from fastapi import APIRouter, Request, HTTPException
import os

from backend.services.schedule_import import (
    parse_csv_text,
    parse_paste_lines,
    upsert_schedule,
    list_schedule_by_date,
)

router = APIRouter(prefix="/api/admin", tags=["admin-import"])

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

def _auth(request: Request):
    token = request.headers.get("x-admin-token", "")
    if not ADMIN_PASSWORD or token != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="unauthorized")


@router.post("/import/schedule_csv")
async def import_schedule_csv(request: Request):
    """
    Body: { "csv": "race_date,meet,race_no,start_time,pdf_url,note\n20260105,1,1,11:00,..." }
    """
    _auth(request)
    body = await request.json()
    csv_text = (body.get("csv") or "").strip()
    rows = parse_csv_text(csv_text)
    result = upsert_schedule(rows)
    return result


@router.post("/import/schedule_paste")
async def import_schedule_paste(request: Request):
    """
    Body: { "text": "복붙텍스트...", "default_date": "20260105", "default_meet": 1 }
    """
    _auth(request)
    body = await request.json()
    text = (body.get("text") or "").strip()
    default_date = body.get("default_date")
    default_meet = body.get("default_meet")

    rows = parse_paste_lines(
        text,
        default_date=default_date,
        default_meet=int(default_meet) if default_meet is not None else None,
    )
    result = upsert_schedule(rows)
    return result


@router.get("/schedule")
def get_schedule(request: Request, race_date: str, meet: int | None = None):
    _auth(request)
    items = list_schedule_by_date(race_date=race_date, meet=meet)
    return {"ok": True, "items": items}
