# backend/routes/predict.py

from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from backend.db.conn import get_conn
from backend.routes.kpi_status import get_kpi_status

router = APIRouter(prefix="/api", tags=["predict"])


class PredictRequest(BaseModel):
    race_id: str
    model: str = "A"


@router.post("/predict")
def predict(req: PredictRequest):
    kpi = get_kpi_status()

    if kpi["status"] == "RED":
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

    conn = get_conn()
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
