from fastapi import APIRouter
from season import SeasonManager
from datetime import datetime

router = APIRouter(prefix="/ui/api/dashboard", tags=["dashboard"])


@router.get("/overview")
def dashboard_overview():
    season_info = SeasonManager.get_status()

    # 예시로 predictions 수를 반환 (원래 DB 연동 시 여기에 쿼리 로직 들어감)
    # 지금은 테스트 용도로 static 숫자 사용
    totals = {
        "predictions": 2250,
        "predictions_with_result": 1234
    }

    return {
        "season": season_info,
        "totals": totals
    }
