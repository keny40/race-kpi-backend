import sqlite3
from datetime import datetime

DB_PATH = "races.db"

def update_prediction_performance(race_id: str):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("""
        SELECT decision FROM predictions
        WHERE race_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    """, (race_id,))
    row = cur.fetchone()

    if not row:
        con.close()
        return

    decision = row[0]

    cur.execute("SELECT winner FROM results WHERE race_id = ?", (race_id,))
    result = cur.fetchone()
    if not result:
        con.close()
        return

    winner = result[0]

    if decision == "PASS":
        outcome = "PASS"
    elif decision == winner:
        outcome = "HIT"
    else:
        outcome = "MISS"

    cur.execute("""
        UPDATE predictions
        SET outcome = ?
        WHERE race_id = ?
    """, (outcome, race_id))

    con.commit()
    con.close()
