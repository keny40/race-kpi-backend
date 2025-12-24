import sqlite3
import os

DB_PATH = "/tmp/races.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
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
