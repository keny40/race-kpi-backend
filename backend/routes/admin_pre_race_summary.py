from fastapi import APIRouter

router = APIRouter(tags=["admin-pre-race"])

@router.get("/summary")
def get_pre_race_summary(limit: int = 5):
    return {
        "items": [],
        "limit": limit
    }
