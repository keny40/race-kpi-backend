import random
from datetime import datetime, timedelta, timezone
from .storage import _connect

STRATEGIES = [
    "baseline",
    "threshold_055",
    "threshold_060",
    "streak_guard",
    "aggressive"
]

def inject_dummy_data(n: int = 300):
    con = _connect()
    cur = con.cursor()

    now = datetime.now(timezone.utc)

    for i in range(n):
        strategy = random.choice(STRATEGIES)
        confidence = round(random.uniform(0.45, 0.75), 3)

        passed = 1 if confidence < 0.55 else 0
        is_hit = None if passed else random.choices([0, 1], weights=[55, 45])[0]

        created_at = now - timedelta(
            days=random.randint(0, 90),
            minutes=random.randint(0, 1440)
        )

        cur.execute("""
            INSERT INTO predictions
            (created_at, race_id, strategy, threshold, exclude_pass,
             passed, predicted_horse_no, confidence, ranking_json)
            VALUES (?, ?, ?, ?, 1, ?, ?, ?, '{}')
        """, (
            created_at.isoformat(),
            f"DUMMY-{strategy}-{i}",
            strategy,
            0.55,
            passed,
            None if passed else random.randint(1, 10),
            confidence
        ))

        pid = cur.lastrowid

        if is_hit is not None:
            cur.execute("""
                INSERT INTO feedback
                (created_at, prediction_id, actual_winner_horse_no, is_hit)
                VALUES (?, ?, ?, ?)
            """, (
                created_at.isoformat(),
                pid,
                random.randint(1, 10),
                is_hit
            ))

    con.commit()
    con.close()
