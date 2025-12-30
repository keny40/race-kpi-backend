from fastapi import APIRouter
import sqlite3

router = APIRouter(prefix="/api/admin/logs", tags=["admin-logs"])

DB_PATH = "data/admin_logs.db"

@router.get("")
def get_logs(limit: int = 50):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute(
        "SELECT * FROM admin_logs ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()

    conn.close()
    return [dict(r) for r in rows]
