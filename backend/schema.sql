PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS predictions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  race_id TEXT NOT NULL,
  decision TEXT NOT NULL,         -- "P" | "B" | "PASS"
  confidence REAL NOT NULL,       -- 0.0 ~ 1.0
  model_name TEXT NOT NULL,       -- e.g. "MODEL_A"
  created_at TEXT NOT NULL        -- ISO8601
);

CREATE INDEX IF NOT EXISTS idx_predictions_race_id ON predictions(race_id);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at);

CREATE TABLE IF NOT EXISTS actual_results (
  race_id TEXT PRIMARY KEY,
  actual_label TEXT NOT NULL,     -- "P" | "B"
  note TEXT DEFAULT NULL,
  created_at TEXT NOT NULL        -- ISO8601
);

CREATE TABLE IF NOT EXISTS kpi_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asof_at TEXT NOT NULL,          -- ISO8601
  total INTEGER NOT NULL,
  hit INTEGER NOT NULL,
  miss INTEGER NOT NULL,
  pass_cnt INTEGER NOT NULL,
  hit_rate REAL NOT NULL,         -- hit / (hit + miss) when denom>0 else 0
  pass_rate REAL NOT NULL         -- pass / total when total>0 else 0
);

CREATE INDEX IF NOT EXISTS idx_kpi_snapshot_asof ON kpi_snapshot(asof_at);
