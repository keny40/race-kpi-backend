from fastapi import APIRouter
from backend.services.predict_service import run_today_prediction

router = APIRouter()

@router.post("/api/today/run")
def today_run():
    score_df = load_today_scores()   # 기존 로직
    combos = run_today_prediction(score_df)
    return combos
