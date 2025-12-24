from fastapi import APIRouter, HTTPException
from datetime import datetime
from backend.db.conn import get_conn
import traceback

router = APIRouter(
    prefix="/api/result",
    tags=["actual"]
)

@router.post("/actual")
def post_actual(payload: dict):
    try:
        race_id = payload["race_id"]
        winner = payload["winner"]
        placed = payload.get("placed")  # optional

        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT OR REPLACE INTO race_actuals
            (race_id, winner, placed, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                race_id,
                winner,
                placed,
                datetime.utcnow().isoformat()
            )
        )

        conn.commit()
        conn.close()

        return {"status": "ok"}

    except Exception as e:
        # Render 로그 + Swagger 양쪽에 에러 노출
        print("🔥 RESULT_ACTUAL ERROR")
        print(traceback.format_exc())

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
