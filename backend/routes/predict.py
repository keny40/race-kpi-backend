from fastapi import APIRouter, HTTPException, Query
import random

from backend.services.db import get_conn
from backend.services.risk_guard import (
    PASS_THRESHOLD,
    get_state,
    on_pass,
    on_run,
    get_risk_multiplier,
)

router = APIRouter(prefix="/api", tags=["predict"])


@router.post("/predict")
def predict(race_id: str = Query(...)):
    state = get_state()

    if state["paused"] == 1:
        raise HTTPException(
            status_code=503,
            detail=f"PAUSED: {state['reason']}"
        )

    horse_no = random.randint(1, 14)
    confidence = round(random.random(), 4)

    conn = get_conn()

    # PASS (confidence 기준)
    if confidence < PASS_THRESHOLD:
        conn.execute(
            """
            INSERT INTO predictions(race_id, predicted_horse_no, confidence, passed)
            VALUES (?, ?, ?, 1)
            """,
            (race_id, horse_no, confidence),
        )
        conn.commit()
        conn.close()
        on_pass(confidence)

        return {
            "race_id": race_id,
            "action": "PASS",
            "confidence": confidence,
        }

    # RUN → RED 단계별 주문 정책
    multiplier = get_risk_multiplier(state["red_streak"] + 1)

    # FORCE PASS
    if multiplier == 0.0:
        conn.execute(
            """
            INSERT INTO predictions(race_id, predicted_horse_no, confidence, passed)
            VALUES (?, ?, ?, 1)
            """,
            (race_id, horse_no, confidence),
        )
        conn.commit()
        conn.close()

        return {
            "race_id": race_id,
            "action": "FORCE_PASS",
            "confidence": confidence,
            "reason": "RED_LIMIT_REACHED",
        }

    # 정상 RUN
    conn.execute(
        """
        INSERT INTO predictions(race_id, predicted_horse_no, confidence, passed)
        VALUES (?, ?, ?, 0)
        """,
        (race_id, horse_no, confidence),
    )
    conn.commit()
    conn.close()

    on_run(confidence)

    return {
        "race_id": race_id,
        "action": "RUN",
        "confidence": confidence,
        "order_multiplier": multiplier,
    }
