import os
import sqlite3
from datetime import datetime
from pathlib import Path

import requests

RED_SCORE_LIMIT = float(os.getenv("RED_SCORE_LIMIT", "3.0"))
RED_CONF_THRESHOLD = float(os.getenv("RED_CONF_THRESHOLD", "0.55"))
RED_DECAY = float(os.getenv("RED_DECAY", "0.5"))
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
DB_PATH = DATA_DIR / "admin_logs.db"

STATE = {
    "run_mode": "ACTIVE",   # ACTIVE | PAUSED
    "paused": False,
    "force_pass": False,
    "red_score": 0.0,
    "last_updated": None,
}

def _utc():
    return datetime.utcnow().isoformat()

def _ensure_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT NOT NULL,
            detail TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn

def log_event(event: str, detail: str):
    try:
        conn = _ensure_db()
        conn.execute(
            "INSERT INTO admin_logs (event, detail, created_at) VALUES (?, ?, ?)",
            (event, detail, _utc())
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

def fetch_logs(limit: int = 50):
    try:
        conn = _ensure_db()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        rows = cur.execute(
            "SELECT id, event, detail, created_at FROM admin_logs ORDER BY id DESC LIMIT ?",
            (int(limit),)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []

def _slack_notify(text: str):
    if not SLACK_WEBHOOK_URL:
        return
    try:
        requests.post(SLACK_WEBHOOK_URL, json={"text": text}, timeout=3)
    except Exception:
        pass

def get_status():
    return {
        "run_mode": STATE["run_mode"],
        "paused": STATE["paused"],
        "force_pass": STATE["force_pass"],
        "red_score": round(float(STATE["red_score"]), 2),
        "last_updated": STATE["last_updated"],
        "thresholds": {
            "red_score_limit": RED_SCORE_LIMIT,
            "red_conf_threshold": RED_CONF_THRESHOLD,
            "red_decay": RED_DECAY,
        }
    }

def set_run_mode(mode: str, reason: str = "MANUAL"):
    if mode == "paused":
        STATE["run_mode"] = "PAUSED"
        STATE["paused"] = True
        STATE["last_updated"] = _utc()
        log_event("RUN_MODE", f"PAUSED ({reason})")
    elif mode == "active":
        STATE["run_mode"] = "ACTIVE"
        STATE["paused"] = False
        STATE["red_score"] = 0.0
        STATE["last_updated"] = _utc()
        log_event("RUN_MODE", f"ACTIVE ({reason})")

def set_force_pass(on: bool, reason: str = "MANUAL"):
    STATE["force_pass"] = bool(on)
    STATE["last_updated"] = _utc()
    log_event("FORCE_PASS", f"{STATE['force_pass']} ({reason})")

def record_prediction(decision: str, confidence: float):
    auto_paused = False
    conf = float(confidence)

    if decision == "RED" and conf >= RED_CONF_THRESHOLD:
        gain = round(conf, 2)
        STATE["red_score"] = float(STATE["red_score"]) + gain
        log_event("RED_SCORE_UP", f"decision=RED conf={conf} gain={gain} score={round(STATE['red_score'],2)}")
    else:
        before = float(STATE["red_score"])
        STATE["red_score"] = max(0.0, before - RED_DECAY)
        if before != STATE["red_score"]:
            log_event("RED_SCORE_DOWN", f"decision={decision} conf={conf} score={round(STATE['red_score'],2)}")

    STATE["last_updated"] = _utc()

    if float(STATE["red_score"]) >= RED_SCORE_LIMIT and STATE["run_mode"] != "PAUSED":
        set_run_mode("paused", reason="AUTO_PAUSE")
        auto_paused = True
        log_event("AUTO_PAUSE", f"score={round(STATE['red_score'],2)} limit={RED_SCORE_LIMIT} conf_th={RED_CONF_THRESHOLD}")
        _slack_notify(
            "🚨 AUTO_PAUSE 발생\n"
            f"- score: {round(STATE['red_score'],2)} / limit: {RED_SCORE_LIMIT}\n"
            f"- conf_th: {RED_CONF_THRESHOLD}\n"
            f"- time: {STATE['last_updated']}"
        )

    return {
        "red_score": round(float(STATE["red_score"]), 2),
        "auto_paused": auto_paused,
    }
