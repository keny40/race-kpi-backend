from fastapi import APIRouter
from backend.services.kpi_store import get_predict_history

router = APIRouter(prefix="/api", tags=["predict-history"])

@router.get("/predict_history/{race_id}")
def history(race_id: str):
    return {
        "ok": True,
        "history": get_predict_history(race_id)
    }
