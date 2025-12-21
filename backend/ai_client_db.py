from __future__ import annotations
import sqlite3
import os
from typing import Dict, Any

from .feature_engine import feature_based_predict


def _db_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "races.db")


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(
        _db_path(),
        timeout=5.0,
        check_same_thread=False
    )
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    return con


def _ensure_table(con: sqlite3.Connection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            race_id INTEGER,
            horse_no INTEGER,
            label TEXT,
            confidence REAL,
            db_weight REAL,
            pass_threshold REAL,
            reason TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    con.commit()


def call_model_DB(payload: Dict[str, Any]) -> Dict[str, Any]:
    race_id = payload.get("race_id")
    horse_no = payload.get("horse_no")

    # 입력 자체가 테스트용이면 무조건 PASS
    if race_id == 0 or horse_no == 0:
        return {
            "label": "PASS",
            "confidence": 0.0,
            "meta": {"reason": "test_input"}
        }

    con = _connect()
    try:
        _ensure_table(con)

        result = feature_based_predict(con, int(race_id), int(horse_no))

        # 🔴 INSERT 실패해도 예측 응답은 살려둔다
        try:
            meta = result.get("meta", {})
            con.execute(
                """
                INSERT INTO predictions
                (race_id, horse_no, label, confidence, db_weight, pass_threshold, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    race_id,
                    horse_no,
                    result.get("label"),
                    result.get("confidence"),
                    meta.get("db_weight"),
                    meta.get("pass_threshold"),
                    meta.get("reason"),
                ),
            )
            con.commit()
        except Exception as e:
            result.setdefault("meta", {})
            result["meta"]["db_error"] = str(e)

        return result

    finally:
        con.close()
