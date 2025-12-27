from backend.db.conn import get_conn


def init_strategy_state():
    con = get_conn()
    cur = con.cursor()

    # 테이블 생성 (이미 있으면 무시)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS strategy_state (
            strategy TEXT PRIMARY KEY,
            enabled INTEGER NOT NULL DEFAULT 0,
            weight_multiplier REAL DEFAULT 1.0,
            updated_at TEXT
        )
    """)

    # FORCE_PASS 기본 전략 등록 (없을 때만)
    cur.execute("""
        INSERT OR IGNORE INTO strategy_state
        (strategy, enabled, weight_multiplier, updated_at)
        VALUES ('FORCE_PASS', 0, 1.0, datetime('now'))
    """)

    con.commit()
    con.close()
