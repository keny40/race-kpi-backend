from fastapi import APIRouter

router = APIRouter(prefix="/api/actual", tags=["actual"])

@router.post("")
def post_actual(
    race_id: str,
    winner: int,
    payout: float,
):
    # 🔥 여기서 import (중요)
    from backend.services.kpi_store import record_result

    record_result(
        race_id=race_id,
        winner=winner,
        payout=payout,
    )

    return {"ok": True}
