# backend/routes/predict.py

from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import os

from backend.services.state_guard import get_system_state

DB_PATH = os.getenv("DB_PATH", "races.db")

router = APIRouter(prefix="/api", tags=["predict"])


class PredictRequest(BaseModel):
    race_id: str
    model: str = "A"


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.post("/predict")
def predict(req: PredictRequest):
    system_state = get_system_state()

    # 🔴 RED 상태 → 강제 PASS
    if system_state == "RED":
        return {
            "race_id": req.race_id,
            "decision": "PASS",
            "confidence": 0,
            "meta": {
                "reason": "kpi_status_red",
                "status": "RED"
            }
        }

    # 정상 예측 (더미 로직)
    decision = "B"
    confidence = 0.61

    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO predictions (race_id, decision, confidence, model, created_at)
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
