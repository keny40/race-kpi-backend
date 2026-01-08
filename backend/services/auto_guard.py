import sqlite3
from typing import Dict

DB_PATH = "backend/races.db"

WINDOW = 20
MIN_HIT_RATE = 0.20
IMMEDIATE_EV_THRESHOLD = -0.1
CONSEC_MISS_LIMIT = 5


def evaluate_and_apply_guard() -> Dict[str, float]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT live_ev, hit_miss
        FROM pre_race_run_history
        WHERE hit_miss IS NOT NULL
          AND live_ev IS NOT NULL
        ORDER BY run_at DESC
        LIMIT ?
        """,
        (WINDOW,),
    ).fetchall()

    if len(rows) < 5:
        conn.close()
        return {"forced": 0, "reason": "insufficient_data"}

    evs = [r["live_ev"] for r in rows]
    avg_ev = sum(evs) / len(evs)

    hits = sum(1 for r in rows if r["hit_miss"] == "HIT")
    hit_rate = hits / len(rows)

    consec_miss = 0
    for r in rows:
        if r["hit_miss"] == "MISS":
            consec_miss += 1
        else:
            break

    forced = 0
    reason = "normal"

    if avg_ev < IMMEDIATE_EV_THRESHOLD or consec_miss >= CONSEC_MISS_LIMIT:
        forced = 1
        reason = "immediate_stop"
    elif avg_ev < 0 and hit_rate < MIN_HIT_RATE:
        forced = 1
        reason = "conditional_stop"

    cur.execute(
        """
        UPDATE pre_race_run_history
        SET forced_pass = ?
        """,
        (forced,),
    )

    conn.commit()
    conn.close()

    return {
        "forced": forced,
        "avg_ev": round(avg_ev, 4),
        "hit_rate": round(hit_rate, 4),
        "consec_miss": consec_miss,
        "reason": reason,
    }
