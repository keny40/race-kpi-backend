from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.strategy_state import is_force_pass_enabled

router = APIRouter(prefix="/api/predict", tags=["predict"])


class PredictRequest(BaseModel):
    race_id: str | None = None


@router.post("")
def predict(req: PredictRequest):
    # FORCE PASS 최우선
    if is_force_pass_enabled():
        return {
            "decision": "PASS",
            "reason": "FORCE_PASS",
            "confidence": 0.0,
        }

    # (임시 기본 응답 – 기존 로직이 있으면 여기 아래에 두세요)
    return {
        "decision": "RUN",
        "reason": "NORMAL",
        "confidence": 0.7,
    }
