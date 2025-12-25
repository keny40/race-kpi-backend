from fastapi import APIRouter
from pydantic import BaseModel
import sqlite3
from datetime import datetime

router = APIRouter(prefix="/api/result", tags=["actual"])

DB_PATH = "backend/races.db"

class ActualRequest(BaseModel):
    race_id: str
    winner: str
    placed: str | None = None
    payoff: float | None = None
    race_date: str | None = None

@router.post("/actual")
def post_actual(req: ActualRequest):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO race_actuals
        (race_id, winner, placed, payoff, race_date, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        req.race_id,
        req.winner,
        req.placed,
        req.payoff,
        req.race_date,
        datetime.utcnow().isoformat()
    ))

    con.commit()
    con.close()

    return {
        "status": "ok",
        "race_id": req.race_id
    }
