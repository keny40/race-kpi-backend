# backend/routes/predict.py

from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import os

from backend.services.state_guard import get_system_state
from backend.services.slack_notifier import send_slack_alert

DB_PATH = os.getenv("DB_PATH", "/tmp/races.db")

router = APIRouter(prefix="/api", tags=["predict"])


class PredictRequest(BaseModel):
    race_id: str
    model: str = "A"


@router.post("/predict")
def predict(req: PredictRequest):
    # 1️⃣ 현재 시스템 상태 확인 (GREEN / YELLOW / RED)
    state = get_system_state()

    # 2️⃣ RED면 → 예측 차단 + Slack 알림 + PASS 반환
    if state == "RED":
        send_slack_alert(
            title="🚨 SYSTEM RED – Prediction Blocked",
            message=f"""
• race_id: {req.race_id}
• action: prediction blocked
• reason: continuous KPI degradation
• returned: PASS
"""
        )

        return {
            "race_id": req.race_id,
            "decision": "PASS",
            "confidence": 0.0,
            "meta": {
                "system_state": "RED",
                "reason": "auto_block"
            }
        }

    # 3️⃣ 정상 예측 로직 (예시)
    decision = "B"
    confidence = 0.61

    # 4️⃣ 예측 DB 저장
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
        "confidence": confidence,
        "meta": {
            "system_state": state
        }
    }
