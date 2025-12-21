# backend/feature_engine.py
from __future__ import annotations
import sqlite3
from typing import Dict, Any, Tuple

Label = str  # "P" | "B"

# --------------------------------------------------
# 가중치 설정 (운영 중 조정 대상)
# --------------------------------------------------
WEIGHTS = {
    "entries": 0.35,
    "odds": 0.45,
    "gate": 0.20,
}

# odds 범위 클램프
ODDS_MIN = 1.0
ODDS_MAX = 50.0


def _normalize(v: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.0
    return max(0.0, min(1.0, (v - lo) / (hi - lo)))


def _get_row(con: sqlite3.Connection, race_id: int, horse_no: int) -> Dict[str, Any]:
    """
    기대 테이블 (자동 탐색)
    - race_features / races / entries 중 하나
    필수 컬럼 후보:
      entries, odds, gate
    """
    tables = ["race_features", "races", "entries"]
    for t in tables:
        try:
            row = con.execute(
                f"""
                SELECT *
                FROM {t}
                WHERE race_id = ? AND horse_no = ?
                """,
                (race_id, horse_no),
            ).fetchone()
            if row:
                return dict(row)
        except Exception:
            continue
    raise RuntimeError("DB feature row not found (race_id, horse_no)")


def compute_feature_score(row: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
    """
    feature → score (0~1)
    """
    # entries (출주 수 적을수록 유리)
    entries = float(row.get("entries", 0))
    entries_score = 1.0 - _normalize(entries, 5, 18)

    # odds (낮을수록 유리)
    odds = float(row.get("odds", ODDS_MAX))
    odds = max(ODDS_MIN, min(ODDS_MAX, odds))
    odds_score = 1.0 - _normalize(odds, ODDS_MIN, ODDS_MAX)

    # gate (중앙 게이트 선호 예시)
    gate = float(row.get("gate", 0))
    gate_score = 1.0 - abs(gate - 6) / 6.0
    gate_score = max(0.0, min(1.0, gate_score))

    score = (
        entries_score * WEIGHTS["entries"]
        + odds_score * WEIGHTS["odds"]
        + gate_score * WEIGHTS["gate"]
    )

    return score, {
        "entries": entries_score,
        "odds": odds_score,
        "gate": gate_score,
    }


def feature_based_predict(
    con: sqlite3.Connection,
    race_id: int,
    horse_no: int,
) -> Dict[str, Any]:
    """
    반환 포맷:
    {
      label: "P" | "B",
      confidence: 0~1,
      feature_detail: {...}
    }
    """
    row = _get_row(con, race_id, horse_no)
    score, detail = compute_feature_score(row)

    label: Label = "P" if score >= 0.5 else "B"
    confidence = abs(score - 0.5) * 2  # 0~1

    return {
        "label": label,
        "confidence": round(confidence, 4),
        "feature_score": round(score, 4),
        "feature_detail": detail,
    }
