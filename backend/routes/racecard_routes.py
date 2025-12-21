from fastapi import APIRouter, HTTPException
import requests

router = APIRouter(prefix="/api", tags=["RaceCard"])

@router.get("/raceCard/{race_id}")
def get_race_card(race_id: int):
    """
    KRA raceCard JSON을 그대로 프론트에 전달
    """
    try:
        url = f"https://race.kra.co.kr/apiData/raceCard/{race_id}.json"
        res = requests.get(url, timeout=5)

        if res.status_code != 200:
            raise HTTPException(status_code=404, detail="KRA raceCard 정보를 불러올 수 없습니다.")

        return res.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
