from fastapi import APIRouter, Query
from backend.managers.season import SeasonManager

router = APIRouter()

# 1️⃣ 최근 결과 리스트 조회
@router.get("/dashboard/recent")
def get_recent_results(limit: int = Query(20, ge=1, le=100)):
    return {
        "status": "ok",
        "message": "최근 결과 조회 성공",
        "limit": limit,
        "data": []
    }

# 2️⃣ 대시보드 요약 정보
@router.get("/dashboard/overview")
def get_dashboard_overview():
    return {
        "status": "ok",
        "message": "대시보드 개요 데이터 조회 성공",
        "summary": {
            "hit": 58,
            "miss": 42,
            "pass": 20,
            "accuracy": 0.58
        }
    }

# 3️⃣ 시즌 관리 관련 API (예시)
@router.get("/dashboard/seasons")
def get_season_list():
    return {
        "status": "ok",
        "message": "시즌 목록 조회 성공",
        "seasons": SeasonManager.list_seasons()
    }
