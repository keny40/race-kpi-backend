import sqlite3
from typing import Optional

DB_PATH = "backend/races.db"
STAKE = 1.0


def calculate_live_ev(hit_miss: str, odds: Optional[float]) -> Optional[float]:
    if hit_miss == "HIT" and odds is not None:
        payout = odds * STAKE
        return (payout - STAKE) / STAKE
    elif hit_miss == "MISS":
        return -1.0
    return None


def update_live_ev_for_race(race_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT rowid, hit_miss, odds
        FROM pre_race_run_history
        WHERE race_id = ?
          AND hit_miss IS NOT NULL
        """,
        (race_id,),
    ).fetchall()

    for r in rows:
        live_ev = calculate_live_ev(r["hit_miss"], r["odds"])
        if live_ev is None:
            continue

        cur.execute(
            """
            UPDATE pre_race_run_history
            SET live_ev = ?
            WHERE rowid = ?
            """,
            (live_ev, r["rowid"]),
        )

    conn.commit()
    conn.close()
