import sqlite3

DB_PATH = "races.db"

schema = """
CREATE TABLE IF NOT EXISTS races (
    race_id TEXT PRIMARY KEY,
    rc_date TEXT,
    meet INTEGER,
    rc_no INTEGER
);

CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id TEXT,
    horse_no INTEGER,
    win_odds REAL,
    rank INTEGER
);

CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id TEXT,
    decision INTEGER,
    confidence REAL,
    created_at TEXT
);
"""

if __name__ == "__main__":
    con = sqlite3.connect(DB_PATH)
    con.executescript(schema)
    con.close()
    print("DB initialized")
