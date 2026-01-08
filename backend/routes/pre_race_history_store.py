import json
import sqlite3
from datetime import datetime
from backend.services.db import get_conn


def save_pre_race_history(
    race_id: str,
    summary: dict,
    confidence: float,
    decision: str,
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO pre_race_run_history (
            race_id,
            run_at,
            summary_json,
            confidence,
            decision,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            race_id,
            datetime.utcnow().isoformat(),
            json.dumps(summary, ensure_ascii=False),
            float(confidence),
            decision,
            datetime.utcnow().isoformat(),
        ),
    )

    conn.commit()
