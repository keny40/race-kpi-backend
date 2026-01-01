from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional

DB_PATH = "ops.db"


def _conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_ops_db():
    con = _conn()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ops_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            level TEXT NOT NULL,
            category TEXT NOT NULL,
            message TEXT NOT NULL,
            payload_json TEXT
        )
    """)
    con.commit()
    con.close()


def add_log(level: str, category: str, message: str, payload_json: Optional[str] = None) -> Dict[str, Any]:
    con = _conn()
    cur = con.cursor()
    ts = datetime.utcnow().isoformat()
    cur.execute(
        "INSERT INTO ops_logs (ts, level, category, message, payload_json) VALUES (?, ?, ?, ?, ?)",
        (ts, level, category, message, payload_json),
    )
    con.commit()
    rowid = cur.lastrowid
    con.close()
    return {"id": rowid, "ts": ts, "level": level, "category": category, "message": message}


def list_logs(limit: int = 200) -> List[Dict[str, Any]]:
    con = _conn()
    cur = con.cursor()
    rows = cur.execute(
        "SELECT id, ts, level, category, message, payload_json FROM ops_logs ORDER BY id DESC LIMIT ?",
        (int(limit),),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def clear_logs() -> Dict[str, Any]:
    con = _conn()
    cur = con.cursor()
    cur.execute("DELETE FROM ops_logs")
    con.commit()
    con.close()
    return {"status": "cleared"}
