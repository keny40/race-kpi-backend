import sqlite3
import os
from fastapi import APIRouter

router = APIRouter()
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "races.db")


def _get_db():
    return sqlite3.connect(DB_PATH)


def _ensure_tables(con):
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS system_lock (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            locked INTEGER,
            reason TEXT,
            updated_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lock_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            reason TEXT,
            created_at TEXT
        )
    """)
    cur.execute("""
        INSERT OR IGNORE INTO system_lock
        VALUES (1, 0, '', '')
    """)
    con.commit()


@router.get("/api/admin/lock")
def get_lock():
    con = _get_db()
    try:
        _ensure_tables(con)
        cur = con.cursor()
        cur.execute(
            "SELECT locked, reason, updated_at FROM system_lock WHERE id=1"
        )
        locked, reason, updated_at = cur.fetchone()
        return {
            "locked": bool(locked),
            "reason": reason,
            "updated_at": updated_at,
        }
    finally:
        con.close()


@router.get("/api/admin/lock/history")
def get_lock_history(limit: int = 20):
    con = _get_db()
    try:
        _ensure_tables(con)
        cur = con.cursor()
        cur.execute("""
            SELECT level, reason, created_at
            FROM lock_history
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        rows = cur.fetchall()
        return [
            {"level": r[0], "reason": r[1], "created_at": r[2]}
            for r in rows
        ]
    finally:
        con.close()


@router.post("/api/admin/lock/release")
def release_lock():
    con = _get_db()
    try:
        _ensure_tables(con)
        cur = con.cursor()
        cur.execute("""
            UPDATE system_lock
            SET locked=0, reason='', updated_at=''
            WHERE id=1
        """)
        con.commit()
        return {"ok": True}
    finally:
        con.close()
