from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from backend.db.conn import get_conn
from backend.services.strategy_state import is_force_pass_enabled
from backend.ai_ensemble import ensemble_predict

router = APIRouter(prefix="/api/predict", tags=["predict"])


class PredictRequest(BaseModel):
    race_id: str
    horses: list[int]


@router.post("")
def predict(req: PredictRequest):
    # 🔴 FORCE PASS 체크 (최우선)
    if is_force_pass_enabled():
        decision = "PASS"
        confidence = 1.0
        reason = "FORCED_BY_ADMIN"

    else:
        # 정상 예측 로직
        result = ensemble_predict(req.horses)
        decision = result["decision"]
        confidence = result["confidence"]
        reason = result.get("reason", "MODEL_DECISION")

    # DB 저장
    con = get_conn()
    cur = con.cursor()
    cur.execute(
        """
        INSERT INTO predictions
        (race_id, decision, confidence, reason, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            req.race_id,
            decision,
            confidence,
            reason,
            datetime.utcnow().isoformat(),
        ),
    )
    con.commit()
    con.close()

    return {
        "race_id": req.race_id,
        "decision": decision,
        "confidence": confidence,
        "reason": reason,
    }
