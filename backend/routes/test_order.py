from fastapi import APIRouter, HTTPException
from backend.services.order_gate import send_order
from backend.services.risk_guard import (
    get_state,
    get_risk_multiplier,
)

router = APIRouter(prefix="/api/test", tags=["test"])


@router.post("/order")
def test_order():
    """
    RED 단계별 주문 금액 제어
    - RED 1 : 100%
    - RED 2 : 50%
    - RED 3 : 0% (FORCE PASS)
    """
    state = get_state()
    red_streak = int(state["red_streak"])
    paused = int(state["paused"])

    # PAUSE 상태면 주문 차단
    if paused == 1:
        raise HTTPException(
            status_code=503,
            detail=f"PAUSED: {state.get('reason','')}"
        )

    base_amount = 1000
    multiplier = get_risk_multiplier(red_streak)

    # FORCE PASS (주문 0원)
    if multiplier == 0.0:
        return {
            "action": "FORCE_PASS",
            "reason": "RED_LIMIT_REACHED",
            "base_amount": base_amount,
            "applied_amount": 0,
            "red_streak": red_streak,
        }

    applied_amount = int(base_amount * multiplier)

    order = {
        "race_id": "TEST_RACE",
        "horse_no": 1,
        "amount": applied_amount,
    }

    result = send_order(order)

    return {
        "action": "ORDER_SENT",
        "red_streak": red_streak,
        "multiplier": multiplier,
        "base_amount": base_amount,
        "applied_amount": applied_amount,
        "order_result": result,
    }
