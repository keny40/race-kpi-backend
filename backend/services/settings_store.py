# backend/services/settings_store.py
import sqlite3
from typing import Dict, Any, Optional
from backend.services.db import DB_PATH

DEFAULTS = {
    "AUTO_PRERACE_IMMEDIATE": "1",   # 업로드 즉시 실행
    "AUTO_PRERACE_BEFORE_MIN": "10", # 출발 n분 전 실행
}

def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_tables():
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS collect_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    conn.commit()

    # defaults seed (upsert)
    for k, v in DEFAULTS.items():
        cur.execute("""
            INSERT INTO collect_settings(key, value)
            VALUES(?, ?)
            ON CONFLICT(key) DO NOTHING
        """, (k, v))
    conn.commit()
    conn.close()

def get_setting(key: str, default: Optional[str] = None) -> str:
    ensure_tables()
    conn = _conn()
    cur = conn.cursor()
    row = cur.execute("SELECT value FROM collect_settings WHERE key=?", (key,)).fetchone()
    conn.close()
    if row is None:
        return default if default is not None else DEFAULTS.get(key, "")
    return str(row["value"])

def set_setting(key: str, value: str) -> None:
    ensure_tables()
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO collect_settings(key, value)
        VALUES(?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
    """, (key, str(value)))
    conn.commit()
    conn.close()

def get_all() -> Dict[str, Any]:
    ensure_tables()
    conn = _conn()
    cur = conn.cursor()
    rows = cur.execute("SELECT key, value FROM collect_settings").fetchall()
    conn.close()
    out: Dict[str, Any] = {}
    for r in rows:
        out[str(r["key"])] = str(r["value"])
    return out
