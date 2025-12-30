from fastapi import APIRouter, HTTPException
from datetime import datetime
from backend.services.operation_guard import (
    get_status,
    record_prediction
)

router = APIRouter(prefix="/api", tags=["predict"])

@router.get("/predict")
@router.post("/predict")
def predict():
    state = get_status()

    # 1️⃣ PAUSE 가드
    if state["paused"] or state["run_mode"] == "PAUSED":
        raise HTTPException(
            status_code=403,
            detail="PAUSED: predict blocked"
        )

    # 2️⃣ FORCE PASS
    if state["force_pass"]:
        return {
            "decision": "PASS",
            "confidence": 0.0,
            "reason": "FORCE_PASS",
            "timestamp": datetime.utcnow().isoformat()
        }

    # 3️⃣ 예측 예시 (테스트용)
    decision = "RED"
    confidence = 0.63

    red_info = record_prediction(decision, confidence)

    return {
        "decision": decision,
        "confidence": confidence,
        "red_score": red_info["red_score"],
        "auto_paused": red_info["auto_paused"],
        "run_mode": get_status()["run_mode"],
        "timestamp": datetime.ut
