BEGIN;

-- 기존 predictions 테이블이 없으면, 아래 CREATE만 쓰셔도 됩니다
-- (이미 있는 경우를 대비해 v2로 새로 만들고 copy하는 방식)

CREATE TABLE IF NOT EXISTS predictions_v2 (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  race_id TEXT NOT NULL,
  strategy TEXT NOT NULL DEFAULT 'BASE',
  predicted_horse_no INTEGER,
  confidence REAL NOT NULL DEFAULT 0.0,
  calibrated_confidence REAL,
  passed INTEGER NOT NULL DEFAULT 0,
  stake REAL NOT NULL DEFAULT 0.0,
  odds REAL,
  payout REAL,
  profit REAL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  meta_json TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_predictions_v2_race_strategy
  ON predictions_v2(race_id, strategy);

-- 구 predictions가 존재하면 copy (컬럼명이 다를 수 있어, 존재할 때만 수행)
-- SQLite는 IF EXISTS INSERT 구문이 없어, 운영상 아래는 수동으로 선택 실행 권장입니다
-- 상황 A: 기존 predictions가 있고, 최소한 race_id / confidence / passed / predicted_horse_no가 있다면
-- INSERT INTO predictions_v2 (race_id, strategy, predicted_horse_no, confidence, passed, created_at)
-- SELECT race_id, COALESCE(strategy,'BASE'), predicted_horse_no, confidence, passed, created_at
-- FROM predictions;

-- 기존 predictions를 v2로 교체
DROP TABLE IF EXISTS predictions;
ALTER TABLE predictions_v2 RENAME TO predictions;

COMMIT;
