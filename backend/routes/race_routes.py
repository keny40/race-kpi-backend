from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict

router = APIRouter(prefix="/races", tags=["Races"])

class Race(BaseModel):
    id: int
    title: str
    date: str

# 데모용 고정 레이스 데이터 (KRA 실제 API 대체)
RACES_TODAY: List[Race] = [
    Race(id=2024113001, title="서울 1R 국3 1000M", date="2024-11-30"),
    Race(id=2024113002, title="서울 2R 국4 1200M", date="2024-11-30"),
    Race(id=2024113005, title="서울 5R 국1 1800M", date="2024-11-30"),
]

class HorseInfo(BaseModel):
    number: int
    name: str
    jockey: str

# race_id별 말 정보 (예: 마번/마명/기수)
HORSES_BY_RACE: Dict[int, List[HorseInfo]] = {
    2024113005: [
        HorseInfo(number=1, name="선행질주", jockey="김기수"),
        HorseInfo(number=2, name="직선추입", jockey="박기수"),
        HorseInfo(number=3, name="안정페이스", jockey="이기수"),
        HorseInfo(number=4, name="역전의명수", jockey="최기수"),
    ]
}

@router.get("/today", response_model=List[Race])
def get_today_races():
    """오늘의 경주 목록 (데모용 고정 데이터)"""
    return RACES_TODAY