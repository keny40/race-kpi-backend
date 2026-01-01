# backend/routes/mock.py
from fastapi import APIRouter

from backend.services.mock_race_data import generate_mock_race
from backend.services.log_store import insert_log
from backend.services.strategy_state import is_force_pass

router = APIRouter(prefix="/api/mock", tags=["mock"])

@router.post("/run")
def run_mock_once():
    race = generate_mock_race()

    insert_log(
        action="MOCK_RUN_API",
        level="INFO",
        detail={
            "race_id": race["race_id"],
            "track": race["track"],
            "race_no": race["race_no"],
            "winner": race["winner"],
            "force_pass": is_force_pass(),
        },
    )

    return {
        "status": "ok",
        "race": race,
    }
