from fastapi import APIRouter
from backend.services.auto_guard import evaluate_and_apply_guard

router = APIRouter(prefix="/api/admin/guard", tags=["admin-guard"])


@router.get("/status")
def get_guard_status():
    try:
        return evaluate_and_apply_guard()
    except Exception as e:
        # 운영 안정성 최우선: 절대 500 반환하지 않음
        return {
            "forced": 0,
            "avg_ev": None,
            "hit_rate": None,
            "consec_miss": None,
            "reason": f"guard_not_ready: {str(e)}"
        }
