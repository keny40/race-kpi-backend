# backend/services/season_reset.py
import sqlite3
from backend.services.log_store import insert_log

DB_PATH = "races.db"

def reset_season():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("DELETE FROM strategy_weights")
    cur.execute("DELETE FROM admin_logs")
    cur.execute("UPDATE risk_state SET red_streak=0, paused=0")

    conn.commit()
    conn.close()

    insert_log("SEASON_RESET", {})
