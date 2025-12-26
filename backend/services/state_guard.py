# backend/services/state_guard.py

import sqlite3
import os
import requests
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "races.db")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

RED_THRESHOLD = 0.4
YELLOW_THRESHOLD = 0.55
RED_CONSECUTIVE_LIMIT = 3


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_system_state():
    conn = _conn()
    cur = conn.cursor()

    row = cur.execute("""
        SELECT
            SUM(CASE WHEN result='HIT' THEN 1 ELSE 0 END) AS hit,
            SUM(CASE WHEN result='MISS' THEN 1 ELSE 0 END) AS miss
        FROM v_race_match
    """).fetchone()

    conn.close()

    hit = row["hit"] or 0
    miss = row["miss"] or 0
    total = hit + miss
    accuracy = hit / total if total > 0 else 0

    if accuracy < RED_THRESHOLD:
        status = "RED"
    elif accuracy < YELLOW_THRESHOLD:
        status = "YELLOW"
    else:
        status = "GREEN"

    return {
        "status": status,
        "accuracy": round(accuracy, 3),
        "hit": hit,
        "miss": miss,
        "total": total
    }


def notify_slack(message: str):
    if not SLACK_WEBHOOK_URL:
        return
    requests.post(SLACK_WEBHOOK_URL, json={"text": message})


def guard_and_notify():
    state = get_system_state()

    if state["status"] == "RED":
        notify_slack(
            f"🚨 KPI RED\n"
            f"Accuracy: {state['accuracy']}\n"
            f"HIT: {state['hit']} / MISS: {state['miss']}"
        )

    return state
