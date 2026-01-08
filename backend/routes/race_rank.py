# backend/routes/race_rank.py
from fastapi import APIRouter, Query
from backend.services.race_ranker import get_race_rankings

router = APIRouter(prefix="/api/race", tags=["race-ai"])

@router.get("/ranking")
def race_ranking(race_id: str = Query(...)):
    return {
        "ok": True,
        "race_id": race_id,
        "races": get_race_rankings(race_id)
    }
