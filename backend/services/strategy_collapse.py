# backend/services/strategy_collapse.py
import sqlite3
from backend.services.risk_guard import force_pause
from backend.services.log_store import insert_log

DB_PATH = "races.db"

MIN_HIT = 0.35
DOMINANCE = 0.7

def detect_collapse():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT strategy, COUNT(*) cnt
        FROM predictions
        WHERE created_at >= datetime('now','-30 minutes')
        GROUP BY strategy
    """).fetchall()

    total = sum(r[1] for r in rows)
    if total == 0:
        return

    for s, c in rows:
        if c / total > DOMINANCE:
            insert_log("STRATEGY_DOMINANCE", {"strategy": s, "ratio": c/total})
            force_pause("STRATEGY_DOMINANCE")
            return

    hit = cur.execute("""
        SELECT AVG(CASE WHEN decision=winner THEN 1 ELSE 0 END)
        FROM predictions p
        JOIN actual_results a ON p.race_id=a.race_id
        WHERE p.created_at >= datetime('now','-30 minutes')
    """).fetchone()[0]

    if hit is not None and hit < MIN_HIT:
        insert_log("GLOBAL_HIT_DROP", {"hit": hit})
        force_pause("GLOBAL_HIT_DROP")

    conn.close()
