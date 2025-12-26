import sqlite3
import os

DB_PATH = "races.db"

def bootstrap_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 실결과 테이블
    cur.execute("""
    CREATE TABLE IF NOT EXISTS race_actuals (
        race_id TEXT PRIMARY KEY,
        winner TEXT NOT NULL,
        placed TEXT,
        payoff REAL,
        race_date TEXT,
        created_at TEXT
    )
    """)

    # 예측 테이블 (이미 있더라도 안전)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        race_id TEXT NOT NULL,
        decision TEXT,
        confidence REAL,
        model TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()
