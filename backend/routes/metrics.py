from fastapi import APIRouter
import sqlite3
import os

router = APIRouter(prefix="/metrics", tags=["metrics"])

DB_PATH = os.getenv("DB_PATH", "races.db")

def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

@router.get("")
def metrics():
    conn = _conn()
    cur = conn.cursor()

    logs = cur.execute("SELECT COUNT(*) c FROM ops_logs").fetchone()["c"]
    runs = cur.execute("SELECT COUNT(*) c FROM ops_runs").fetchone()["c"]
    reds = cur.execute(
        "SELECT COUNT(*) c FROM ops_runs WHERE is_red=1"
    ).fetchone()["c"]

    conn.close()

    return (
        f"ops_logs_total {logs}\n"
        f"ops_runs_total {runs}\n"
        f"ops_red_total {reds}\n"
    )
