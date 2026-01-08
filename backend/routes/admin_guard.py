from fastapi import APIRouter
from backend.services.auto_guard import evaluate_and_apply_guard

router = APIRouter(prefix="/api/admin/guard", tags=["admin-guard"])


@router.get("/status")
def get_guard_status():
    result = evaluate_and_apply_guard()
    return result
