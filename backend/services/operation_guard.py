from datetime import datetime
import os
import requests

RED_SCORE_LIMIT = float(os.getenv("RED_SCORE_LIMIT", "3.0"))
RED_CONF_THRESHOLD = float(os.getenv("RED_CONF_THRESHOLD", "0.55"))
RED_DECAY = float(os.getenv("RED_DECAY", "0.5"))
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

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

def _slack_notify(text: str):
    if not SLACK_WEBHOOK_URL:
        return
    try:
        requests.post(
            SLACK_WEBHOOK_URL,
            json={"text": text},
            timeout=3
        )
    except Exception:
        pass

def record_prediction(decision: str, confidence: float):
    auto_paused = False

    if decision == "RED" and confidence >= RED_CONF_THRESHOLD:
        STATE["red_score"] += round(confidence, 2)
    else:
        STATE["red_score"] = max(0.0, STATE["red_score"] - RED_DECAY)

    if STATE["red_score"] >= RED_SCORE_LIMIT:
        set_run_mode("paused", reason="AUTO_PAUSE")
        auto_paused = True

        _slack_notify(
            "🚨 AUTO_PAUSE 발생\n"
            f"- RED score: {STATE['red_score']}\n"
            f"- threshold: {RED_SCORE_LIMIT}\n"
            f"- confidence >= {RED_CONF_THRESHOLD}\n"
            f"- time: {STATE['last_updated']}"
        )

    return {
        "red_score": round(STATE["red_score"], 2),
        "auto_paused": auto_paused,
    }
