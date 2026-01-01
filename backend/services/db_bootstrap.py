# backend/services/db_bootstrap.py
import sqlite3
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "races.db"


def bootstrap_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # =========================
    # Scheduler 상태 (ON / OFF / RUN / PAUSE)
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS scheduler_state (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        running INTEGER DEFAULT 0,
        paused INTEGER DEFAULT 0,
        mode TEXT DEFAULT 'MOCK',
        interval_sec INTEGER DEFAULT 5,
        last_run_at TEXT,
        updated_at TEXT
    )
    """)

    cur.execute("""
    INSERT OR IGNORE INTO scheduler_state (id, running, paused, mode, interval_sec, updated_at)
    VALUES (1, 0, 0, 'MOCK', 5, ?)
    """, (datetime.utcnow().isoformat(),))

    # =========================
    # Risk Guard 상태
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS risk_state (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        score REAL DEFAULT 0.0,
        threshold REAL DEFAULT 0.75,
        streak INTEGER DEFAULT 0,
        is_red INTEGER DEFAULT 0,
        reason TEXT,
        paused INTEGER DEFAULT 0,
        updated_at TEXT
    )
    """)

    cur.execute("""
    INSERT OR IGNORE INTO risk_state
    (id, score, threshold, streak, is_red, paused, updated_at)
    VALUES (1, 0.0, 0.75, 0, 0, 0, ?)
    """, (datetime.utcnow().isoformat(),))

    # =========================
    # RED 원인 Feature 로그
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS risk_features (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_at TEXT,
        f_html_text_too_short INTEGER DEFAULT 0,
        f_table_count_low INTEGER DEFAULT 0,
        f_row_count_low INTEGER DEFAULT 0,
        raw_features TEXT
    )
    """)

    # =========================
    # 관리자 액션 로그 (ON / OFF / RUN / RESET)
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admin_action_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        result TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

    print(f"[DB] bootstrap completed: {DB_PATH}")
