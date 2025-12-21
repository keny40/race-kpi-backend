import sqlite3

DB_PATH = "races.db"

DDL = """
CREATE TABLE IF NOT EXISTS seasons (
  season_id TEXT PRIMARY KEY,
  started_at TEXT,
  locked INTEGER DEFAULT 0,
  lock_reason TEXT,
  lock_until TEXT,
  is_current INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS season_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  season_id TEXT,
  event_type TEXT,
  payload TEXT,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS prediction_models (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  prediction_id INTEGER,
  race_id TEXT,
  model_name TEXT,
  label TEXT,
  score REAL,
  weight REAL,
  created_at TEXT
);
"""

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(DDL)
    conn.commit()
    conn.close()
    print("DB migrated: seasons / season_events / prediction_models ready")

if __name__ == "__main__":
    main()
