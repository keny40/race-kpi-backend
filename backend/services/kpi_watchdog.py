# backend/services/kpi_watchdog.py
import sqlite3
from typing import Dict
from backend.services.alert_slack import alert_strategy_drop
from backend.services.run_mode import get_mode

DB_PATH = "races.db"
HIT_ALERT = 0.35
ROI_ALERT = 0.95
WINDOW = 80

def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def evaluate_and_alert():
    conn = _conn()
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT p.strategy,
               AVG(CASE WHEN p.decision = a.winner THEN 1.0 ELSE 0.0 END) AS hit_rate,
               AVG(COALESCE(p.roi,1.0)) AS avg_roi,
               COUNT(*) AS cnt
        FROM predictions p
        JOIN actual_results a ON p.race_id = a.race_id
        GROUP BY p.strategy
        HAVING cnt >= ?
    """, (WINDOW,)).fetchall()
    conn.close()

    for r in rows:
        if r["hit_rate"] < HIT_ALERT or r["avg_roi"] < ROI_ALERT:
            alert_strategy_drop(r["strategy"], r["hit_rate"], r["avg_roi"])
