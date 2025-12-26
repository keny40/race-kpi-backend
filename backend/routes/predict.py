# backend/routes/predict.py

from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import os

from backend.services.state_manager import get_current_state
from backend.services.pdf_generator import generate_kpi_pdf
from backend.services.slack_notifier import send_slack_file

DB_PATH = "/tmp/races.db"

router = APIRouter(prefix="/api", tags=["predict"])


class PredictRequest(BaseModel):
    race_id: str
    model: str = "A"


@router.post("/predict")
def predict(req: PredictRequest):
    """
    B-5
    - RED 상태면 무조건 PASS 반환
    - PASS 발생 시 PDF 자동 생성 + Slack 전송
    """

    state = get_current_state()  # RED / YELLOW / GREEN

    # 🔴 RED → 강제 PASS
    if state == "RED":
        decision = "PASS"
        confidence = 0.0

        # DB 저장
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
            "FORCED_PASS",
            datetime.utcnow().isoformat()
        ))
        con.commit()
        con.close()

        # PDF 생성 + Slack 첨부
        pdf_path = generate_kpi_pdf(reason="RED_FORCED_PASS")
        send_slack_file(
            text=f"🚨 RED 상태 → 예측 강제 PASS 발생 (race_id={req.race_id})",
            file_path=pdf_path
        )

        return {
            "race_id": req.race_id,
            "decision": "PASS",
            "confidence": 0.0,
            "state": "RED",
            "reason": "forced_pass"
        }

    # 🟡🟢 정상 예측 로직 (예시)
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
        "confidence": confidence,
        "state": state
    }
