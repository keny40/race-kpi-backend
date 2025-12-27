import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "races.db")

def bootstrap_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 기존 테이블들 ...
    cur.execute("""
    CREATE TABLE IF NOT EXISTS system_status_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        status TEXT,
        created_at TEXT
    )
    """)

    # ✅ 관리자 액션 로그 테이블 (이번에 추가)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admin_action_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        value TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()
