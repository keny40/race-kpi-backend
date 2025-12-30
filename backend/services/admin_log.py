import sqlite3
from datetime import datetime

DB_PATH = "races.db"


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def log_admin_action(action: str, detail: str = ""):
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO admin_logs (created_at, action, detail)
        VALUES (?, ?, ?)
        """,
        (datetime.utcnow().isoformat(), action, detail),
    )
    conn.commit()
    conn.close()


def get_logs(limit: int = 100):
    conn = _conn()
    cur = conn.cursor()
    rows = cur.execute(
        """
        SELECT created_at, action, detail
        FROM admin_logs
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
