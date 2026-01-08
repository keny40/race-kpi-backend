import json
import sqlite3
from typing import Dict, Any

DB_PATH = "races.db"


def save_actual_result(result: Dict[str, Any]) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO actual_results
        (race_id, winner, top3, field_size, fetched_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        result["race_id"],
        result["features"]["winner"],
        json.dumps(result["features"]["top3"]),
        result["features"]["field_size"],
        result["fetched_at"],
    ))

    conn.commit()
    conn.close()
