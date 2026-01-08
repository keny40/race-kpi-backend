from backend.services.run_mode import get_mode
from backend.services.risk_guard import is_paused
from backend.services.log_store import insert_log


def send_order(order: dict):
    # 1. PAUSE 최우선 차단
    if is_paused():
        insert_log(
            action="ORDER_BLOCKED",
            detail="PAUSED",
            message=str(order)
        )
        return {
            "status": "BLOCKED",
            "reason": "PAUSED",
            "order": order
        }

    # 2. DRY_RUN 차단
    if get_mode() != "LIVE":
        insert_log(
            action="ORDER_BLOCKED",
            detail="DRY_RUN",
            message=str(order)
        )
        return {
            "status": "BLOCKED",
            "reason": "DRY_RUN",
            "order": order
        }

    # 3. LIVE 통과
    insert_log(
        action="ORDER_SENT",
        detail="LIVE",
        message=str(order)
    )

    # TODO: 실제 계좌 주문 연동 위치
    return {
        "status": "SENT",
        "order": order
    }
