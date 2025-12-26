# backend/services/state_guard.py

import os
import sqlite3

DB_PATH = os.getenv("DB_PATH", "races.db")

# 상태 캐시 (메모리)
_last_status = None
_red_streak = 0

# 알림 기준
RED_STREAK_THRESHOLD = int(os.getenv("RED_STREAK_THRESHOLD", "3"))


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_system_state():
    """
    KPI 기반 시스템 상태 계산
    """
    global _last_status, _red_streak

    conn = _conn()
    cur = conn.cursor()

    row = cur.execute("""
        SELECT
            SUM(CASE WHEN result='HIT' THEN 1 ELSE 0 END) AS hit,
            SUM(CASE WHEN result='MISS' THEN 1 ELSE 0 END) AS miss
        FROM v_race_match
        WHERE result IN ('HIT','MISS')
    """).fetchone()

    conn.close()

    hit = row["hit"] or 0
    miss = row["miss"] or 0
    total = hit + miss

    accuracy = hit / total if total > 0 else 0

    # 상태 판단
    if total < 5:
        status = "RED"
    elif accuracy >= 0.6:
        status = "GREEN"
    elif accuracy >= 0.45:
        status = "YELLOW"
    else:
        status = "RED"

    # RED 연속 횟수 계산
    if status == "RED":
        _red_streak += 1
    else:
        _red_streak = 0

    _last_status = status

    return {
        "status": status,
        "accuracy": round(accuracy, 3),
        "hit": hit,
        "miss": miss,
        "total": total,
        "red_streak": _red_streak,
        "should_alert": _red_streak >= RED_STREAK_THRESHOLD
    }
