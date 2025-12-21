from fastapi import APIRouter
import sqlite3

router = APIRouter()
DB_PATH = "races.db"

@router.post("/manual")
def manual_result(race_id: str, winner: str, payoff: float = 0):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute(
        """
        INSERT OR REPLACE INTO results (race_id, winner, payoff)
        VALUES (?, ?, ?)
        """,
        (race_id, winner, payoff),
    )

    con.commit()
    con.close()

    return {"status": "ok", "race_id": race_id}
