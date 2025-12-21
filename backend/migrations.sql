CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    race_id INTEGER NOT NULL,
    horse_no INTEGER NOT NULL,

    label TEXT NOT NULL,
    confidence REAL NOT NULL,

    db_weight REAL,
    pass_threshold REAL,

    reason TEXT,

    hit INTEGER,              -- 1=적중, 0=실패, NULL=미정
    actual_label TEXT         -- 실제 결과(P/B 등)
);

CREATE INDEX IF NOT EXISTS idx_predictions_race
ON predictions (race_id, horse_no);
