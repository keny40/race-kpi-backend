import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, "races.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    _ensure_schema(conn)
    return conn

def _ensure_schema(conn):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS race_actuals (
        race_id TEXT PRIMARY KEY,
        winner TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    conn.commit()
