from backend.services.db import get_conn
from typing import Dict

def update_odds(odds_map: Dict[str, float]):
    conn = get_conn()
    cur = conn.cursor()

    for race_id, odds in odds_map.items():
        cur.execute(
            """
            UPDATE pre_race_run_history
            SET odds = ?
            WHERE race_id = ?
            """,
            (odds, race_id),
        )

    conn.commit()
