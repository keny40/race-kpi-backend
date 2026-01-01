# backend/services/admin_audit.py

import os
import sqlite3
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "races.db")


def _conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def ensure_admin_actions_table():
    con = _conn()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            action TEXT NOT NULL,
            result TEXT NOT NULL,
            message TEXT
        )
    """)
    con.commit()
    con.close()


def log_action(action: str, result: str, message: str = ""):
    """
    ✅ 4) 운영 로그 DB 영구 저장
    """
    ensure_admin_actions_table()

    con = _conn()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO admin_actions (ts, action, result, message) VALUES (?, ?, ?, ?)",
        (datetime.utcnow().isoformat(), action, result, message),
    )
    con.commit()
    con.close()


def list_actions(limit: int = 200):
    ensure_admin_actions_table()

    con = _conn()
    cur = con.cursor()
    rows = cur.execute(
        "SELECT id, ts, action, result, message FROM admin_actions ORDER BY id DESC LIMIT ?",
        (int(limit),),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]
