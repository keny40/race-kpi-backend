from fastapi import APIRouter

router = APIRouter(
    prefix="/api/result",
    tags=["result"]
)

@router.post("/actual")
def post_actual(payload: dict):
    return {
        "status": "ok",
        "race_id": payload.get("race_id"),
        "winner": payload.get("winner"),
        "placed": payload.get("placed"),
        "payoff": payload.get("payoff"),
        "race_date": payload.get("race_date"),
    }
