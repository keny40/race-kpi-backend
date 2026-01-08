CREATE TABLE IF NOT EXISTS actual_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id TEXT UNIQUE,
    winner INTEGER,
    top3 TEXT,
    field_size INTEGER,
    fetched_at REAL
);
