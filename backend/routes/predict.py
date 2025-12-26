from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
import sqlite3

DB_PATH = "/tmp/races.db"

router = APIRouter(prefix="/api", tags=["predict"])

class PredictRequest(BaseModel):
    race_id: str
    model: str = "A"

@router.post("/predict")
def predict(req: PredictRequest):
    # 예시 모델 결과
    decision = "B"
    confidence = 0.61

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("""
        INSERT INTO predictions
        (race_id, decision, confidence, model, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        req.race_id,
        decision,
        confidence,
        req.model,
        datetime.utcnow().isoformat()
    ))

    con.commit()
    con.close()

    return {
        "race_id": req.race_id,
        "decision": decision,
        "confidence": confidence
    }
