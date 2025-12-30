from datetime import datetime
import os

RED_SCORE_LIMIT = float(os.getenv("RED_SCORE_LIMIT", "3.0"))
RED_CONF_THRESHOLD = float(os.getenv("RED_CONF_THRESHOLD", "0.55"))
RED_DECAY = float(os.getenv("RED_DECAY", "0.5"))

STATE = {
    "run_mode": "ACTIVE",
    "paused": False,
    "force_pass": False,
    "red_score": 0.0,
    "last_updated": None,
}

def get_status():
    return STATE

def set_run_mode(mode: str, reason="MANUAL"):
    if mode == "paused":
        STATE["run_mode"] = "PAUSED"
        STATE["paused"] = True
    else:
        STATE["run_mode"] = "ACTIVE"
        STATE["paused"] = False
        STATE["red_score"] = 0.0

    STATE["last_updated"] = datetime.utcnow().isoformat()

def set_force_pass(on: bool):
    STATE["force_pass"] = on

def record_prediction(decision: str, confidence: float):
    """
    RED 판단 고도화 로직

    - RED + confidence >= threshold → 가중치 누적
    - confidence 비례 점수 부여
    - 기준 미달 시 score 감소(decay)
    """
    auto_paused = False

    if decision == "RED" and confidence >= RED_CONF_THRESHOLD:
        gain = round(confidence, 2)
        STATE["red_score"] += gain
    else:
        STATE["red_score"] = max(0.0, STATE["red_score"] - RED_DECAY)

    if STATE["red_score"] >= RED_SCORE_LIMIT:
        set_run_mode("paused", reason="AUTO_PAUSE")
        auto_paused = True

    return {
        "red_score": round(STATE["red_score"], 2),
        "auto_paused": auto_paused,
    }
