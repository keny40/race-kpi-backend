from fastapi import APIRouter
from backend.services.strategy_state import is_force_pass_enabled

router = APIRouter(prefix="/api/predict", tags=["predict"])

@router.post("")
def predict(req: dict):
    if is_force_pass_enabled():
        return {
            "decision": "PASS",
            "reason": "FORCE_PASS"
        }

    # 🔽 기존 예측 로직 유지
    return {
        "decision": "P",
        "reason": "NORMAL"
    }
