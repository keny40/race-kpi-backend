from fastapi import APIRouter
from backend.season import SeasonManager  # ✅ 수정된 import 경로

router = APIRouter(prefix="/ui/api/dashboard", tags=["dashboard"])

@router.get("/overview")
def get_dashboard_overview():
    sm = SeasonManager()
    return {
        "season": sm.get_current_season(),
        "totals": {
            "predictions": sm.total_predictions(),
            "predictions_with_result": sm.total_predictions_with_result()
        }
    }

@router.get("/recent")
def get_recent_predictions(limit: int = 50):
    sm = SeasonManager()
    return sm.fetch_recent_predictions(limit=limit)
