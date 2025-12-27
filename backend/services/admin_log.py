import sqlite3, os
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "races.db")

def log_admin_action(action: str, value: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO admin_action_log (action, value, created_at)
        VALUES (?, ?, ?)
    """, (action, value, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
