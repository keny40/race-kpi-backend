from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import random

from models import model_A, model_B

# ✅ 반드시 먼저 app 생성
app = FastAPI()


# ---------- 데이터 모델 ----------
class Horse(BaseModel):
    horse_id: int
    recent_rank: Optional[int] = None
    draw: Optional[int] = None
    odds: Optional[float] = None


class PredictRequest(BaseModel):
    race_id: int
    distance: Optional[int] = None
    track: Optional[str] = None
    horses: List[Horse]


# ---------- 헬스 체크 ----------
@app.get("/")
def root():
    return {"status": "ai_model-ok"}


# ---------- 예측 ----------
@app.post("/predict")
def predict(req: PredictRequest):
    res_A = model_A(req)
    res_B = model_B(req)

    recommended = "A" if res_A["confidence"] >= res_B["confidence"] else "B"

    return {
        "race_id": req.race_id,
        "conditions": {
            "distance": req.distance,
            "track": req.track
        },
        "models": {
            "A": res_A,
            "B": res_B
        },
        "recommended": recommended
    }
