# backend/routes/admin_settings.py
import sqlite3
import os
from fastapi import APIRouter

router = APIRouter()

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "races.db")


def _get_db():
    return sqlite3.connect(DB_PATH)


def _ensure_table(con):
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            hit_threshold REAL,
            pass_threshold REAL,
            period TEXT,
            auto_stop INTEGER
        )
    """)
    cur.execute("""
        INSERT OR IGNORE INTO admin_settings
        (id, hit_threshold, pass_threshold, period, auto_stop)
        VALUES (1, 0.55, 0.30, 'monthly', 1)
    """)
    con.commit()


@router.get("/api/admin/settings")
def get_settings():
    con = _get_db()
    try:
        _ensure_table(con)
        cur = con.cursor()
        cur.execute("""
            SELECT hit_threshold, pass_threshold, period, auto_stop
            FROM admin_settings WHERE id=1
        """)
        r = cur.fetchone()
        return {
            "hit_threshold": r[0],
            "pass_threshold": r[1],
            "period": r[2],
            "auto_stop": bool(r[3]),
        }
    finally:
        con.close()


@router.post("/api/admin/settings")
def update_settings(payload: dict):
    con = _get_db()
    try:
        _ensure_table(con)
        cur = con.cursor()
        cur.execute("""
            UPDATE admin_settings
            SET hit_threshold=?,
                pass_threshold=?,
                period=?,
                auto_stop=?
            WHERE id=1
        """, (
            payload["hit_threshold"],
            payload["pass_threshold"],
            payload["period"],
            int(payload["auto_stop"])
        ))
        con.commit()
        return {"ok": True}
    finally:
        con.close()
