from fastapi import APIRouter, Query
from backend.season import SeasonManager

router = APIRouter(
    prefix="/ui/api/dashboard",
    tags=["dashboard"]
)

@router.get("/overview")
def get_dashboard_overview():
    sm = SeasonManager()
    return sm.get_overview()

@router.get("/recent")
def get_dashboard_recent(limit: int = Query(50, ge=1, le=100)):
    sm = SeasonManager()
    return sm.get_recent(limit)
