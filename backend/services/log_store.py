# backend/services/log_store.py
import sqlite3
import time
import json
import os
import urllib.request
from typing import Any, Dict, List, Optional

DB_PATH = os.getenv("DB_PATH", "races.db")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "").strip()


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def bootstrap_admin_tables():
    conn = _conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts INTEGER NOT NULL,
            level TEXT NOT NULL,
            action TEXT NOT NULL,
            message TEXT NOT NULL,
            meta_json TEXT NOT NULL DEFAULT '{}'
        )
        """
    )

    conn.commit()
    conn.close()


def _slack_post(text: str) -> None:
    if not SLACK_WEBHOOK_URL:
        return
    payload = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        SLACK_WEBHOOK_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as _:
            pass
    except Exception:
        # Slack 실패가 운영 로직을 깨면 안됨
        return


def insert_log(level: str, action: str, message: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    bootstrap_admin_tables()

    ts = int(time.time())
    meta = meta or {}
    meta_json = json.dumps(meta, ensure_ascii=False)

    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO admin_logs (ts, level, action, message, meta_json) VALUES (?, ?, ?, ?, ?)",
        (ts, level, action, message, meta_json),
    )
    conn.commit()
    log_id = cur.lastrowid
    conn.close()

    row = {"id": log_id, "ts": ts, "level": level, "action": action, "message": message, "meta": meta}

    # ===== A-24: FAIL 실시간 Slack 전송 =====
    if action.upper() == "FAIL":
        race_id = meta.get("race_id", "")
        reason = meta.get("reason", "")
        extra = meta.get("extra", "")
        _slack_post(
            f"🚨 FAIL 발생\nrace_id: {race_id}\nreason: {reason}\nmessage: {message}\nextra: {extra}\n(ts: {ts})"
        )

    # AUTO_PAUSE 같은 운영 이벤트도 Slack에 같이 보냄
    if action.upper() == "AUTO_PAUSE":
        reason = meta.get("reason", "")
        fail_streak = meta.get("fail_streak", "")
        _slack_post(f"⛔ AUTO_PAUSE\nreason: {reason}\nfail_streak: {fail_streak}\n(ts: {ts})")

    return row


def query_logs(limit: int = 200, action: str = "") -> List[Dict[str, Any]]:
    bootstrap_admin_tables()

    conn = _conn()
    cur = conn.cursor()
    if action:
        rows = cur.execute(
            "SELECT * FROM admin_logs WHERE action=? ORDER BY id DESC LIMIT ?",
            (action, limit),
        ).fetchall()
    else:
        rows = cur.execute(
            "SELECT * FROM admin_logs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    conn.close()

    out: List[Dict[str, Any]] = []
    for r in rows:
        try:
            meta = json.loads(r["meta_json"] or "{}")
        except Exception:
            meta = {}
        out.append(
            {
                "id": r["id"],
                "ts": r["ts"],
                "level": r["level"],
                "action": r["action"],
                "message": r["message"],
                "meta": meta,
            }
        )
    return out


def query_logs_csv(limit: int = 500, action: str = "") -> str:
    import csv
    import io

    rows = query_logs(limit=limit, action=action)

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "ts", "level", "action", "message", "meta_json"])
    for r in rows:
        w.writerow([r["id"], r["ts"], r["level"], r["action"], r["message"], json.dumps(r["meta"], ensure_ascii=False)])
    return buf.getvalue()
