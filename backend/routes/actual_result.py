from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.kpi_service import upsert_actual_result, get_actual_result

router = APIRouter(tags=["actual"])

class ActualRequest(BaseModel):
    race_id: str
    winner: str  # horse_no 등을 문자열로 통일

@router.post("/result/actual")
def post_actual(req: ActualRequest):
    return upsert_actual_result(race_id=req.race_id, winner=req.winner)

@router.get("/result/actual")
def get_actual(race_id: str):
    row = get_actual_result(race_id=race_id)
    if not row:
        return {"race_id": race_id, "winner": None}
    return row
