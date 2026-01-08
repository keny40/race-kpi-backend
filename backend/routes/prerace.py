from fastapi import APIRouter, Query
from backend.services.prerace_service import get_prerace_summary

router = APIRouter(prefix="/api/prerace", tags=["prerace"])


@router.get("/summary")
def read_prerace_summary(
    race_id: str = Query(..., description="경주 ID")
):
    return get_prerace_summary(race_id)
