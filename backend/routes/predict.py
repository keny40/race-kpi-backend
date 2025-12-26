# backend/routes/predict.py

from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import os

from backend.services.state_guard import guard_and_notify

DB_PATH = os.getenv("DB_PATH", "races.db")
router = APIRouter(prefix="/api", tags=["predict"])


class PredictRequest(BaseModel):
    race_id: str
    model: str = "A"


@router.post("/predict")
def predict(req: PredictRequest):
    state = guard_and_notify()

    if state["status"] == "RED":
        return {
            "race_id": req.race_id,
            "decision": "PASS",
            "confidence": 0,
            "meta": {
                "reason": "kpi_status_red",
                "status": "RED"
            }
        }

    decision = "B"
    confidence = 0.61

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
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
    conn.commit()
    conn.close()

    return {
        "race_id": req.race_id,
        "decision": decision,
        "confidence": confidence
    }
