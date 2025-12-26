# backend/services/db_bootstrap.py

import sqlite3
import os
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "races.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables(cur):
    # 예측 결과
    cur.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        race_id TEXT NOT NULL,
        decision TEXT NOT NULL,
        confidence REAL NOT NULL,
        model TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # 실제 결과
    cur.execute("""
    CREATE TABLE IF NOT EXISTS race_actuals (
        race_id TEXT PRIMARY KEY,
        winner TEXT NOT NULL,
        placed TEXT,
        payoff REAL,
        race_date TEXT,
        created_at TEXT NOT NULL
    )
    """)


def create_views(cur):
    # 예측 ↔ 실결과 매칭 VIEW (PDF / KPI 공용)
    cur.execute("""
    CREATE VIEW IF NOT EXISTS v_race_match AS
    SELECT
        p.race_id,
        p.decision,
        p.confidence,
        a.winner,
        CASE
            WHEN p.decision = 'PASS' THEN 'PASS'
            WHEN a.winner IS NULL THEN 'PENDING'
            WHEN p.decision = a.winner THEN 'HIT'
            ELSE 'MISS'
        END AS result
    FROM predictions p
    LEFT JOIN race_actuals a
        ON p.race_id = a.race_id
    """)


def bootstrap_db():
    conn = get_conn()
    cur = conn.cursor()

    create_tables(cur)
    create_views(cur)

    conn.commit()
    conn.close()


# 앱 시작 시 자동 실행용
if __name__ == "__main__":
    bootstrap_db()
