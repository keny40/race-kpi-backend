import json
from datetime import datetime
from backend.services.db import get_conn


def save_pre_race_history(
    race_id: str,
    summary: dict,
    confidence: float,
    decision: str,
):
    """
    pre_race_run_history 테이블에 정석 저장
    """
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO pre_race_run_history
        (race_id, run_at, summary_json, confidence, decision)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            race_id,
            datetime.utcnow().isoformat(timespec="seconds"),
            json.dumps(summary, ensure_ascii=False),
            float(confidence),
            decision,
        ),
    )
    conn.commit()
