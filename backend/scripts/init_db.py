import sqlite3

DB_PATH = "races.db"

schema = """
CREATE TABLE IF NOT EXISTS races (
  race_id TEXT PRIMARY KEY,
  race_date TEXT,
  track TEXT,
  distance INTEGER,
  weather TEXT
);

CREATE TABLE IF NOT EXISTS entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  race_id TEXT,
  horse TEXT,
  jockey TEXT,
  trainer TEXT,
  gate INTEGER,
  weight REAL,
  odds REAL
);

CREATE TABLE IF NOT EXISTS results (
  race_id TEXT PRIMARY KEY,
  winner TEXT,
  placed TEXT,
  payoff REAL
);

CREATE TABLE IF NOT EXISTS predictions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  race_id TEXT,
  decision TEXT,
  confidence REAL,
  created_at TEXT
);
"""

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(schema)
    conn.commit()
    conn.close()
    print("races.db created and initialized")
