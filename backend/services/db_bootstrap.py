import sqlite3

DB_PATH = "/tmp/races.db"

def bootstrap_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS race_actuals (
        race_id TEXT PRIMARY KEY,
        winner TEXT NOT NULL,
        placed TEXT,
        payoff REAL,
        race_date TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        race_id TEXT NOT NULL,
        decision TEXT,
        confidence REAL,
        model TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()
