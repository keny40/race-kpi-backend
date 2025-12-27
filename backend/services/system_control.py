import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "races.db")

DEFAULT_STATE = {
    "auto_red": 1,
    "force_pass": 0,
    "red_lock": 0
}


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init():
    conn = _conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS system_control (
        key TEXT PRIMARY KEY,
        value INTEGER
    )
    """)

    for k, v in DEFAULT_STATE.items():
        cur.execute("""
            INSERT OR IGNORE INTO system_control (key, value)
            VALUES (?, ?)
        """, (k, v))

    conn.commit()
    conn.close()


def get_state() -> dict:
    _init()
    conn = _conn()
    cur = conn.cursor()

    rows = cur.execute("SELECT key, value FROM system_control").fetchall()
    conn.close()

    return {r["key"]: bool(r["value"]) for r in rows}


def set_state(key: str, value: bool):
    _init()
    conn = _conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE system_control
        SET value = ?
        WHERE key = ?
    """, (1 if value else 0, key))

    conn.commit()
    conn.close()
