from fastapi import APIRouter, Query
from datetime import date
from backend.routes.timeline import log_event

router = APIRouter()

# 임시 데이터 (실제 DB로 교체 예정)
MOCK_RACE_DATA = {
    "2025121801,5,0": {
        "count": 42,
        "from": date(2024, 11, 1),
        "to": date(2024, 12, 18),
    },
    "121": {
        "count": 18,
        "from": date(2024, 12, 1),
        "to": date(2024, 12, 10),
    },
}

@router.get("/race/exists")
def race_exists(race_id: str = Query(...)):
    data = MOCK_RACE_DATA.get(race_id)

    payload = {
        "exists": bool(data),
        "count": data["count"] if data else 0,
        "from": data["from"] if data else None,
        "to": data["to"] if data else None,
    }

    log_event(
        event_type="exists",
        race_id=race_id,
        payload=payload
    )

    return payload
