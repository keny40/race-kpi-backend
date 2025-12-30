import sqlite3
from datetime import datetime

DB_PATH = "races.db"

def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _ensure_table():
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS system_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    # 기본값 ACTIVE
    cur.execute("""
        INSERT OR IGNORE INTO system_state (key, value, updated_at)
        VALUES ('run_mode', 'ACTIVE', ?)
    """, (datetime.utcnow().isoformat(),))
    conn.commit()
    conn.close()

def get_run_mode() -> str:
    _ensure_table()
    conn = _conn()
    cur = conn.cursor()
    row = cur.execute("SELECT value FROM system_state WHERE key='run_mode'").fetchone()
    conn.close()
    return (row["value"] if row else "ACTIVE") or "ACTIVE"

def set_run_mode(mode: str):
    _ensure_table()
    mode = (mode or "").upper()
    if mode not in ("ACTIVE", "PAUSED"):
        mode = "ACTIVE"
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO system_state (key, value, updated_at)
        VALUES ('run_mode', ?, ?)
        ON CONFLICT(key) DO UPDATE SET
            value=excluded.value,
            updated_at=excluded.updated_at
    """, (mode, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def is_paused() -> bool:
    return get_run_mode().upper() == "PAUSED"
