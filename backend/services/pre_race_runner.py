import json
from datetime import datetime

from backend.services.db import get_conn
from backend.services.rules import get_current_rules


def run_pre_race(race_id: str, decision, confidence: float):
    conn = get_conn()
    rules = get_current_rules()

    if decision is None:
        bet_pass = "PASS"
    else:
        bet_pass = "BET"

    if confidence >= 0.7:
        confidence_bucket = "HIGH"
    elif confidence >= 0.4:
        confidence_bucket = "MID"
    else:
        confidence_bucket = "LOW"

    rule_snapshot = json.dumps(rules, ensure_ascii=False)

    conn.execute(
        """
        INSERT INTO pre_race_run_history (
            race_id,
            run_at,
            confidence,
            confidence_bucket,
            decision,
            bet_pass,
            hit_miss,
            rule_snapshot
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            race_id,
            datetime.utcnow().isoformat(),
            confidence,
            confidence_bucket,
            decision,
            bet_pass,
            None,
            rule_snapshot,
        )
    )

    conn.commit()
