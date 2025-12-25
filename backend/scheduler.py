import sqlite3
import os
import time
import threading
from datetime import datetime, timedelta

#from backend.services.lock_manager import lock_and_notify, unlock_if_expired

DB_PATH = os.path.join(os.path.dirname(__file__), "races.db")

INTERVAL = 60
RED_STREAK_THRESHOLD = 3
CONFIDENCE_THRESHOLD = 0.55
COOLDOWN_MINUTES = 30


def _now():
    return datetime.now()


def run_scheduler_tick():
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.cursor()

        # 상태 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS scheduler_state (
                id INTEGER PRIMARY KEY CHECK (id=1),
                red_score REAL DEFAULT 0,
                last_checked TEXT
            )
        """)
        cur.execute("INSERT OR IGNORE INTO scheduler_state VALUES (1,0,'')")
        con.commit()

        # 최근 예측 confidence 기반 RED 점수 계산
        cur.execute("""
            SELECT confidence
            FROM predictions
            ORDER BY created_at DESC
            LIMIT 10
        """)
        rows = cur.fetchall()

        red_score = 0.0
        for (conf,) in rows:
            if conf < CONFIDENCE_THRESHOLD:
                red_score += 1.0
            else:
                red_score += 0.2

        # 연속성 가중
        if red_score >= 6:
            red_score += 2

        cur.execute(
            "UPDATE scheduler_state SET red_score=?, last_checked=? WHERE id=1",
            (red_score, _now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        con.commit()

        # LOCK 판단
        if red_score >= RED_STREAK_THRESHOLD * 3:
            lock_and_notify(
                con=con,
                reason=f"RED SCORE {red_score:.1f} (confidence+연속)",
                period_for_pdf="monthly",
                pdf_pages=2,
                lock_level="RED",
                window="rolling",
                details=f"confidence<{CONFIDENCE_THRESHOLD}"
            )

        # 자동 해제
        unlock_if_expired(con, cooldown_minutes=COOLDOWN_MINUTES)

    finally:
        con.close()


def start_scheduler():
    def loop():
        while True:
            try:
                run_scheduler_tick()
            except Exception:
                pass
            time.sleep(INTERVAL)

    threading.Thread(target=loop, daemon=True).start()
