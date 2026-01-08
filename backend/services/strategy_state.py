# backend/services/strategy_state.py
import sqlite3
from datetime import datetime

DB_PATH = "races.db"


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# 전략 상태 테이블 보장
# =========================
def _ensure_table():
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS strategy_state (
            strategy TEXT PRIMARY KEY,
            enabled INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


_ensure_table()


# =========================
# 전략 활성 여부 조회
# =========================
def is_enabled(strategy: str) -> bool:
    conn = _conn()
    cur = conn.cursor()
    row = cur.execute(
        "SELECT enabled FROM strategy_state WHERE strategy=?",
        (strategy,)
    ).fetchone()
    conn.close()
    return bool(row["enabled"]) if row else True


# alias (기존 코드 호환)
def is_strategy_enabled(strategy: str) -> bool:
    return is_enabled(strategy)


# =========================
# 전략 ON / OFF 설정
# =========================
def set_strategy_enabled(strategy: str, enabled: bool):
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO strategy_state(strategy, enabled, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(strategy) DO UPDATE SET
            enabled=?,
            updated_at=?
    """, (
        strategy,
        int(enabled),
        datetime.now().isoformat(),
        int(enabled),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


# =========================
# AUTO SWITCH (필수)
# =========================
def auto_switch(strategy: str, allow: bool = True):
    """
    strategy_runner / strategy_guard 호환용
    현재는 enabled 제어로 통합
    """
    set_strategy_enabled(strategy, allow)
