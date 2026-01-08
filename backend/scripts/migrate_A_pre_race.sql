-- A: pre-race 안정화용 테이블 추가
-- SQLite 기준

PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS scheduler_leases (
  name TEXT PRIMARY KEY,
  instance_id TEXT NOT NULL,
  lease_expires_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS pre_race_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  race_id TEXT NOT NULL,
  run_type TEXT NOT NULL,
  scheduled_for TEXT NOT NULL,
  minute_before INTEGER NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL,
  detail TEXT,
  UNIQUE(race_id, run_type, scheduled_for, minute_before)
);

CREATE INDEX IF NOT EXISTS idx_pre_race_runs_race_id ON pre_race_runs(race_id);
CREATE INDEX IF NOT EXISTS idx_pre_race_runs_scheduled_for ON pre_race_runs(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_pre_race_runs_status ON pre_race_runs(status);
