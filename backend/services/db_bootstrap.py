import sqlite3
from backend.services.db import DB_PATH


def bootstrap_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # === predictions ===
    cur.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            race_id TEXT,
            predicted_horse_no INTEGER,
            confidence REAL,
            passed INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # === guard_state ===
    cur.execute("""
        CREATE TABLE IF NOT EXISTS guard_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            red_streak INTEGER DEFAULT 0,
            paused INTEGER DEFAULT 0,
            reason TEXT DEFAULT '',
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    cur.execute("""
        INSERT OR IGNORE INTO guard_state (id, red_streak, paused)
        VALUES (1, 0, 0)
    """)

    # === ops_logs ===
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ops_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT DEFAULT (datetime('now')),
            action TEXT,
            detail TEXT
        )
    """)

    conn.commit()
    conn.close()
