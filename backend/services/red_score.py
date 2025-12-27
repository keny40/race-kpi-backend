import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.getenv("DB_PATH", "races.db")

W_RED = float(os.getenv("RED_WEIGHT", "1.0"))
W_YELLOW = float(os.getenv("YELLOW_WEIGHT", "0.4"))

WINDOW = int(os.getenv("RED_WINDOW", "12"))          # 최근 N회 (점수 계산용)
THRESHOLD = float(os.getenv("RED_SCORE", "3.0"))     # 누적 점수 임계치
DECAY = float(os.getenv("RED_DECAY", "0.85"))        # 감쇠율


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_tables():
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS system_status_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        status TEXT,
        created_at TEXT
    )
    """)
    conn.commit()
    conn.close()


def record_status(status: str):
    _ensure_tables()
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO system_status_log (status, created_at)
        VALUES (?, ?)
    """, (status, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def get_recent_statuses(limit: int = 50):
    _ensure_tables()
    conn = _conn()
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT status, created_at
        FROM system_status_log
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [{"status": r["status"], "created_at": r["created_at"]} for r in rows][::-1]


def calc_red_score(window: int | None = None) -> float:
    _ensure_tables()
    w = window if window is not None else WINDOW

    conn = _conn()
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT status
        FROM system_status_log
        ORDER BY created_at DESC
        LIMIT ?
    """, (w,)).fetchall()
    conn.close()

    score = 0.0
    decay = 1.0

    for r in rows:
        s = r["status"]
        if s == "RED":
            score += W_RED * decay
        elif s == "YELLOW":
            score += W_YELLOW * decay
        decay *= DECAY

    return round(score, 2)


def is_red_locked() -> bool:
    return calc_red_score() >= THRESHOLD


def explain_score(window: int | None = None):
    _ensure_tables()
    w = window if window is not None else WINDOW

    conn = _conn()
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT status, created_at
        FROM system_status_log
        ORDER BY created_at DESC
        LIMIT ?
    """, (w,)).fetchall()
    conn.close()

    parts = []
    decay = 1.0
    total = 0.0

    for r in rows:
        s = r["status"]
        add = 0.0
        if s == "RED":
            add = W_RED * decay
        elif s == "YELLOW":
            add = W_YELLOW * decay
        total += add
        parts.append({
            "status": s,
            "created_at": r["created_at"],
            "decay": round(decay, 4),
            "add": round(add, 4)
        })
        decay *= DECAY

    return {
        "score": round(total, 2),
        "threshold": THRESHOLD,
        "window": w,
        "decay": DECAY,
        "weights": {"RED": W_RED, "YELLOW": W_YELLOW},
        "locked": round(total, 2) >= THRESHOLD,
        "terms": parts[::-1]
    }
