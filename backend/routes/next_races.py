# backend/routes/next_races.py
from fastapi import APIRouter
from backend.services.rpt_data_source import list_races

router = APIRouter(prefix="/api", tags=["races"])

@router.get("/next_races")
def next_races():
    return {
        "ok": True,
        "races": list_races()
    }
