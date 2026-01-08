from fastapi import APIRouter, Query
from backend.services.kpi_store import recommend_threshold

router = APIRouter(prefix="/api/admin/recommend", tags=["admin"])


@router.post("/apply")
def apply_threshold(threshold: float = Query(...)):
    result = recommend_threshold(threshold)
    return result
