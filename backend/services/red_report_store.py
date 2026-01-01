import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

DB_PATH = Path("races.db")

def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def now_iso():
    return datetime.utcnow().isoformat()

def insert_report(
    race_id: str,
    mode: Optional[str],
    risk: Dict[str, Any],
    features: Dict[str, Any],
    meta: Optional[Dict[str, Any]] = None
) -> int:
    """
    risk: evaluate_and_maybe_pause() 결과 dict
    features/meta: 당시 입력 snapshot
    """
    conn = _conn()
    cur = conn.cursor()

    is_red = 1 if risk.get("is_red") else 0
    did_pause = 1 if risk.get("did_pause") else 0

    row = (
        race_id,
        mode,
        is_red,
        float(risk.get("score") or 0.0),
        float(risk.get("threshold") or 0.0),
        int(risk.get("red_streak") or 0),
        did_pause,
        str(risk.get("reason") or ""),
        json.dumps(features or {}, ensure_ascii=False),
        json.dumps(risk.get("contrib") or {}, ensure_ascii=False),
        json.dumps(risk.get("settings") or {}, ensure_ascii=False),
        json.dumps(meta or {}, ensure_ascii=False),
        now_iso()
    )

    cur.execute("""
        INSERT INTO red_reports
        (race_id, mode, is_red, score, threshold, red_streak, did_pause, reason,
         features_json, contrib_json, settings_json, meta_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, row)

    report_id = cur.lastrowid
    conn.commit()
    conn.close()
    return int(report_id)

def list_reports(limit: int = 50) -> List[Dict[str, Any]]:
    conn = _conn()
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT id, race_id, mode, is_red, score, threshold, red_streak, did_pause, reason, created_at
        FROM red_reports
        ORDER BY id DESC
        LIMIT ?
    """, (int(limit),)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_report(report_id: int) -> Dict[str, Any]:
    conn = _conn()
    cur = conn.cursor()
    row = cur.execute("""
        SELECT *
        FROM red_reports
        WHERE id = ?
    """, (int(report_id),)).fetchone()
    conn.close()

    if not row:
        raise KeyError("report_not_found")

    d = dict(row)

    # JSON fields decode
    for k in ["features_json", "contrib_json", "settings_json", "meta_json"]:
        try:
            d[k] = json.loads(d.get(k) or "{}")
        except Exception:
            d[k] = {}

    return d
