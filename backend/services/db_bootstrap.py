import sqlite3

DB_PATH = "races.db"

def bootstrap_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # =========================
    # 기존 경주 데이터 테이블
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS races (
        race_id TEXT PRIMARY KEY,
        rc_date TEXT,
        meet INTEGER,
        rc_no INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        race_id TEXT,
        horse_no INTEGER,
        win_odds REAL,
        rank INTEGER
    )
    """)

    # =========================
    # 예측 결과 저장
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        race_id TEXT,
        model TEXT,
        decision TEXT,
        confidence REAL,
        created_at TEXT
    )
    """)

    # =========================
    # 실측 결과
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS actual_results (
        race_id TEXT PRIMARY KEY,
        winner TEXT
    )
    """)

    # =========================
    # KPI 누적
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS kpi_stats (
        model TEXT PRIMARY KEY,
        hit INTEGER,
        miss INTEGER,
        pass INTEGER
    )
    """)

    con.commit()
    con.close()
