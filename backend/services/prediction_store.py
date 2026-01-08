# backend/services/prediction_store.py
import sqlite3
import json
from typing import Any, Dict, List, Optional

DB_PATH = "races.db"


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def save_prediction(
    race_id: str,
    decision: Any,
    confidence: Optional[float] = None,
    calibrated_confidence: Optional[float] = None,
    roi: Optional[float] = None,
    score: Optional[float] = None,
    strategy: Optional[str] = None,
    reason: Optional[str] = None,
    candidates: Optional[List[Dict[str, Any]]] = None,
):
    """
    predict API에서 호출하는 단일 저장 함수 (표준 엔트리포인트)
    """
    conn = _conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO predictions (
            race_id,
            decision,
            confidence,
            calibrated_confidence,
            roi,
            score,
            strategy,
            reason,
            candidates_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            race_id,
            str(decision) if decision is not None else None,
            confidence,
            calibrated_confidence,
            roi,
            score,
            strategy,
            reason,
            json.dumps(candidates, ensure_ascii=False) if candidates else None,
        ),
    )

    conn.commit()
    conn.close()
