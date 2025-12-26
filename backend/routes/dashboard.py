from fastapi import APIRouter
from backend.managers.season import SeasonManager

router = APIRouter()

@router.get("/dashboard/overview")
def get_overview():
    return {
        "message": "Overview route working",
        "total_races": 123,
        "accuracy": 0.72
    }

@router.get("/dashboard/recent")
def get_recent(limit: int = 50):
    return {
        "message": f"Recent results, limit={limit}",
        "data": []
    }

@router.get("/dashboard/seasons")
def get_seasons():
    return {
        "message": "Seasons loaded",
        "seasons": SeasonManager().get_seasons()
    }
