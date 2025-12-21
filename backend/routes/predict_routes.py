from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from routes.race_routes import HORSES_BY_RACE, HorseInfo

router = APIRouter(prefix="/predict", tags=["Predict"])

class HorsePrediction(BaseModel):
    number: int
    name: str
    jockey: str
    win_rate: float
    place_rate: float

class PredictionResponse(BaseModel):
    race_id: int
    horses: List[HorsePrediction]

@router.get("/{race_id}", response_model=PredictionResponse)
def predict_race(race_id: int):
    """간단한 데모 예측 API (고정 비율)"""
    horses = HORSES_BY_RACE.get(race_id)
    if not horses:
        raise HTTPException(status_code=404, detail="해당 경주의 마번 정보가 없습니다.")

    preds = []
    base_win = 40.0
    base_place = 60.0

    for idx, h in enumerate(horses):
        win = max(5.0, base_win - idx * 8.0)
        place = max(10.0, base_place - idx * 6.0)
        preds.append(
            HorsePrediction(
                number=h.number,
                name=h.name,
                jockey=h.jockey,
                win_rate=round(win, 1),
                place_rate=round(place, 1),
            )
        )

    return PredictionResponse(race_id=race_id, horses=preds)