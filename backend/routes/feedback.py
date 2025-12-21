from fastapi import APIRouter
from pydantic import BaseModel
import sqlite3

DB_PATH = "races.db"
router = APIRouter(prefix="/api/result", tags=["feedback"])

class FeedbackRequest(BaseModel):
    race_id: str
    winner_gate: int
    payoff: float = 1.0

def _conn():
    conn = sqlite3.connect(DB_PATH)
    return conn

@router.post("/feedback")
def feedback(req: FeedbackRequest):
    conn = _conn()
    cur = conn.cursor()

    # winner 컬럼에 게이트를 문자열로 저장(예측 decision과 동일 타입)
    cur.execute(
        """
        INSERT OR REPLACE INTO results (race_id, winner, placed, payoff)
        VALUES (?,?,?,?)
        """,
        (req.race_id, str(req.winner_gate), "", float(req.payoff)),
    )

    conn.commit()
    conn.close()
    return {"status": "OK"}
