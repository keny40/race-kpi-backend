import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "races.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db_if_needed():
    """
    Render / 로컬 공통
    서버 기동 시 운영 DB 자동 초기화
    """
    conn = get_conn()
    cur = conn.cursor()

    # 1️⃣ guard_config 테이블
    cur.execute("""
    CREATE TABLE IF NOT EXISTS guard_config (
        id INTEGER PRIMARY KEY,
        window_size INTEGER,
        min_hit_rate REAL,
        immediate_ev_threshold REAL,
        consec_miss_limit INTEGER
    )
    """)

    cur.execute("""
    INSERT OR IGNORE INTO guard_config
    (id, window_size, min_hit_rate, immediate_ev_threshold, consec_miss_limit)
    VALUES (1, 20, 0.2, -0.1, 5)
    """)

    # 2️⃣ pre_race_run_history 테이블
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pre_race_run_history (
        race_id TEXT PRIMARY KEY,
        run_at TEXT,
        confidence REAL,
        decision TEXT,
        bet_pass TEXT,
        hit_miss TEXT,
        rule_snapshot TEXT,
        confidence_bucket TEXT,
        odds REAL,
        pre_ev REAL,
        live_ev REAL,
        payout REAL DEFAULT 0,
        forced_pass INTEGER DEFAULT 0
    )
    """)

    conn.commit()
