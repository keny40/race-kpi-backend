from fastapi import APIRouter
from pydantic import BaseModel
from backend.routes.kpi_status import get_current_status
from backend.services.red_score import record_status, is_red_locked
from backend.services.system_control import get_state
from backend.services.slack_alert import send_red_alert_with_pdf


router = APIRouter(prefix="/api", tags=["predict"])


class PredictRequest(BaseModel):
    race_id: str
    model: str = "A"


@router.post("/predict")
def predict(req: PredictRequest):
    ctrl = get_state()

    if ctrl["force_pass"]:
        return {
            "race_id": req.race_id,
            "decision": "PASS",
            "confidence": 0.0,
            "meta": {"forced": True}
        }

    status = get_current_status()
    record_status(status)

    if ctrl["auto_red"] and (status == "RED" or is_red_locked()):
        if not ctrl["red_lock"]:
            send_red_alert_with_pdf("RED 가중치 기준 잠금 발생")

        return {
            "race_id": req.race_id,
            "decision": "PASS",
            "confidence": 0.0,
            "meta": {
                "blocked": True,
                "reason": "RED_WEIGHT_LOCK"
            }
        }

    return {
        "race_id": req.race_id,
        "decision": "B",
        "confidence": 0.61
    }
