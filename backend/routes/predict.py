# backend/routes/predict.py

from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "races.db")

router = APIRouter(prefix="/api", tags=["predict"])


class PredictRequest(BaseModel):
    race_id: str
    model: str = "A"


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_kpi_status(cur) -> str:
    """
    RED / YELLOW / GREEN
    """
    row = cur.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN result = 'HIT' THEN 1 ELSE 0 END) AS hit,
            SUM(CASE WHEN result = 'MISS' THEN 1 ELSE 0 END) AS miss
        FROM v_race_match
        WHERE result IN ('HIT', 'MISS')
    """).fetchone()

    total = row["total"] or 0
    hit = row["hit"] or 0
    miss = row["miss"] or 0

    if total < 5:
        return "RED"

    accuracy = hit / total if total > 0 else 0

    if accuracy >= 0.60:
        return "GREEN"
    elif accuracy >= 0.45:
        return "YELLOW"
    else:
        return "RED"


@router.post("/predict")
def predict(req: PredictRequest):
    conn = _conn()
    cur = conn.cursor()

    status = get_kpi_status(cur)

    # 🚨 운영 차단 상태 → PASS 반환
    if status == "RED":
        cur.execute("""
            INSERT INTO predictions
            (race_id, decision, confidence, model, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            req.race_id,
            "PASS",
            0.0,
            req.model,
            datetime.utcnow().isoformat()
        ))
        conn.commit()
        conn.close()

        return {
            "race_id": req.race_id,
            "decision": "PASS",
            "confidence": 0.0,
            "meta": {
                "reason": "kpi_status_red",
                "status": status
            }
        }

    # ✅ 정상 상태 → 기존 예측 로직 (지금은 더미)
    decision = "B"
    confidence = 0.61

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
        "confidence": confidence,
        "meta": {
            "status": status
        }
    }
