from fastapi import APIRouter
from datetime import datetime
from backend.services.db import get_conn

router = APIRouter(prefix="/api/admin/pre-race", tags=["admin-pre-race-settings"])

@router.get("/settings")
def get_settings():
    row = get_conn().execute(
        "SELECT confidence_threshold FROM pre_race_settings LIMIT 1"
    ).fetchone()
    return {"confidence_threshold": row["confidence_threshold"]}

@router.post("/settings")
def save_settings(threshold: float):
    conn = get_conn()
    conn.execute(
        """
        UPDATE pre_race_settings
        SET confidence_threshold=?, updated_at=?
        WHERE id=1
        """,
        (threshold, datetime.utcnow().isoformat())
    )
    conn.commit()
    return {"ok": True}