from fastapi import APIRouter
from datetime import datetime
from backend.db.conn import get_conn

router = APIRouter(prefix="/api/result", tags=["actual"])

@router.post("/actual")
def post_actual(payload: dict):
    race_id = payload["race_id"]
    winner = payload["winner"]

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR REPLACE INTO race_actuals
        (race_id, winner, created_at)
        VALUES (?, ?, ?)
        """,
        (race_id, winner, datetime.utcnow().isoformat())
    )

    conn.commit()
    conn.close()

    return {"status": "ok"}
