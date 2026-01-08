from fastapi import APIRouter, HTTPException
from pathlib import Path
import json

router = APIRouter(prefix="/api/admin", tags=["admin-result"])

RESULT_DIR = Path("data/results")
RESULT_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/result")
def save_result(race_id: str, winner: int):
    path = RESULT_DIR / f"{race_id}.json"
    data = {
        "race_id": race_id,
        "winner": winner
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {"ok": True, "saved": race_id}
