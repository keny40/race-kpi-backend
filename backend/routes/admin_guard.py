from fastapi import APIRouter
from backend.services.auto_guard import (
    evaluate_and_apply_guard,
    force_stop_guard,
    release_guard,
)

router = APIRouter(prefix="/api/admin/guard", tags=["admin-guard"])


@router.get("/status")
def get_guard_status():
    try:
        return evaluate_and_apply_guard()
    except Exception as e:
        return {
            "forced": 0,
            "avg_ev": None,
            "hit_rate": None,
            "consec_miss": None,
            "reason": f"guard_not_ready: {str(e)}",
        }


@router.post("/force-stop")
def force_stop():
    force_stop_guard()
    return {"status": "stopped"}


@router.post("/release")
def release():
    release_guard()
    return {"status": "released"}
