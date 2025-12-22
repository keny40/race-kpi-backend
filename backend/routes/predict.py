from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["predict"])

class PredictRequest(BaseModel):
    race_id: str = "TEST"
    model: str = "A"

@router.post("/predict")
def predict(req: PredictRequest):
    return {
        "race_id": req.race_id,
        "decision": "B",
        "confidence": 0.61
    }
