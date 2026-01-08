# backend/services/race_decision.py
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# =========================
# DB
# =========================
def _db() -> str:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
    return os.path.join(base, "races.db")

def init_decision_tables() -> None:
    conn = sqlite3.connect(_db())
    cur = conn.cursor()

    # settings: threshold mode / value
    cur.execute("""
    CREATE TABLE IF NOT EXISTS app_settings (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TEXT
    )
    """)

    # decisions per race_no within race_id
    cur.execute("""
    CREATE TABLE IF NOT EXISTS race_ai_decisions (
        race_id TEXT,
        race_no INTEGER,
        passed INTEGER,              -- 1=PASS, 0=GO
        threshold REAL,
        confidence REAL,
        top_horse_no INTEGER,
        top_horse_name TEXT,
        top_score REAL,
        second_score REAL,
        reason TEXT,
        updated_at TEXT,
        PRIMARY KEY (race_id, race_no)
    )
    """)

    conn.commit()
    conn.close()


# =========================
# Settings helpers
# =========================
def _set_setting(key: str, value: str) -> None:
    init_decision_tables()
    conn = sqlite3.connect(_db())
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO app_settings(key, value, updated_at)
    VALUES (?, ?, ?)
    ON CONFLICT(key) DO UPDATE SET
      value=excluded.value,
      updated_at=excluded.updated_at
    """, (key, value, datetime.now().isoformat(timespec="seconds")))
    conn.commit()
    conn.close()

def _get_setting(key: str, default: str) -> str:
    init_decision_tables()
    conn = sqlite3.connect(_db())
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    row = cur.execute("SELECT value FROM app_settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row and row["value"] is not None else default


def set_threshold_mode(mode: str) -> Dict[str, Any]:
    """
    mode: "manual" or "auto"
    """
    if mode not in ("manual", "auto"):
        raise ValueError("mode must be 'manual' or 'auto'")
    _set_setting("threshold_mode", mode)
    return {"ok": True, "threshold_mode": mode}

def set_manual_threshold(value: float) -> Dict[str, Any]:
    """
    0~1
    """
    v = max(0.0, min(1.0, float(value)))
    _set_setting("manual_threshold", str(v))
    return {"ok": True, "manual_threshold": v}

def get_threshold_settings() -> Dict[str, Any]:
    mode = _get_setting("threshold_mode", "manual")
    manual = float(_get_setting("manual_threshold", "0.65"))
    return {"threshold_mode": mode, "manual_threshold": manual}


# =========================
# Confidence & threshold logic
# =========================
def _sigmoid(x: float) -> float:
    # 안전한 시그모이드 (overflow 방지)
    if x < -60:
        return 0.0
    if x > 60:
        return 1.0
    import math
    return 1.0 / (1.0 + math.exp(-x))

def compute_confidence_from_scores(top_score: float, second_score: float) -> float:
    """
    CONFIDENCE 정의(고정):
    - top_score 자체가 높을수록 신뢰 증가
    - top-second 마진이 클수록 신뢰 증가

    conf = 0.55 * top_score + 0.45 * sigmoid(12*(margin-0.04))
    """
    ts = max(0.0, min(1.0, float(top_score)))
    ss = max(0.0, min(1.0, float(second_score)))
    margin = max(0.0, ts - ss)

    margin_term = _sigmoid(12.0 * (margin - 0.04))
    conf = 0.55 * ts + 0.45 * margin_term
    return max(0.0, min(1.0, conf))


def _auto_threshold_from_history(default: float = 0.65) -> float:
    """
    자동 기준선(간단/안정형):
    - horse_scores 기반 confidence 분포의 상위 분위로 잡으면 PASS가 늘고, 하위면 GO가 늘어남
    - 여기서는 '최근 생성된 decisions'가 있으면 그 confidence의 중앙값+0.05를 사용
    - 없으면 default
    """
    init_decision_tables()
    conn = sqlite3.connect(_db())
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute("""
    SELECT confidence
    FROM race_ai_decisions
    WHERE confidence IS NOT NULL
    ORDER BY updated_at DESC
    LIMIT 200
    """).fetchall()

    conn.close()
    if not rows:
        return float(default)

    vals = [float(r["confidence"]) for r in rows if r["confidence"] is not None]
    if not vals:
        return float(default)

    vals.sort()
    mid = vals[len(vals)//2]  # median
    thr = mid + 0.05
    # 너무 공격/보수로 쏠리지 않게 클램프
    thr = max(0.45, min(0.85, thr))
    return float(thr)


def resolve_threshold() -> Tuple[float, str]:
    s = get_threshold_settings()
    mode = s["threshold_mode"]
    if mode == "manual":
        return float(s["manual_threshold"]), "manual"
    return _auto_threshold_from_history(), "auto"


# =========================
# Decision compute
# =========================
def _fetch_ranked_entries(race_id: str) -> List[sqlite3.Row]:
    """
    race_entries + horse_scores join
    - race_ranker.py가 정렬하긴 하지만 여기서도 score desc 기준으로 race_no 단위로 처리
    """
    conn = sqlite3.connect(_db())
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute("""
    SELECT
        e.race_no,
        e.horse_no,
        e.horse_name,
        COALESCE(s.score, 0.0) AS score
    FROM race_entries e
    LEFT JOIN horse_scores s
      ON e.horse_name = s.horse_name
    WHERE e.race_id = ?
    ORDER BY e.race_no ASC, score DESC
    """, (race_id,)).fetchall()

    conn.close()
    return rows


def compute_race_decisions(race_id: str) -> Dict[str, Any]:
    """
    race_id에 포함된 모든 race_no에 대해
    - top/second score → confidence 계산
    - threshold 비교 → PASS/GO 결정
    - DB 저장
    """
    init_decision_tables()

    threshold, mode = resolve_threshold()

    rows = _fetch_ranked_entries(race_id)
    if not rows:
        return {"ok": False, "reason": "no race_entries for race_id", "race_id": race_id}

    # race_no별 그룹
    grouped: Dict[int, List[Dict[str, Any]]] = {}
    for r in rows:
        grouped.setdefault(int(r["race_no"]), []).append({
            "horse_no": int(r["horse_no"]),
            "horse_name": str(r["horse_name"]),
            "score": float(r["score"]),
        })

    now = datetime.now().isoformat(timespec="seconds")
    out_items = []

    conn = sqlite3.connect(_db())
    cur = conn.cursor()

    for race_no, items in grouped.items():
        # items already score-desc due to SQL
        top = items[0] if len(items) >= 1 else None
        second = items[1] if len(items) >= 2 else None

        if not top:
            continue

        top_score = float(top["score"])
        second_score = float(second["score"]) if second else 0.0
        confidence = compute_confidence_from_scores(top_score, second_score)

        passed = 1 if confidence < threshold else 0
        reason = f"{mode}: conf={confidence:.3f} vs thr={threshold:.3f}"

        cur.execute("""
        INSERT INTO race_ai_decisions (
            race_id, race_no, passed, threshold, confidence,
            top_horse_no, top_horse_name, top_score, second_score,
            reason, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(race_id, race_no) DO UPDATE SET
            passed=excluded.passed,
            threshold=excluded.threshold,
            confidence=excluded.confidence,
            top_horse_no=excluded.top_horse_no,
            top_horse_name=excluded.top_horse_name,
            top_score=excluded.top_score,
            second_score=excluded.second_score,
            reason=excluded.reason,
            updated_at=excluded.updated_at
        """, (
            race_id, race_no, passed, threshold, confidence,
            int(top["horse_no"]), str(top["horse_name"]), top_score, second_score,
            reason, now
        ))

        out_items.append({
            "race_no": race_no,
            "passed": bool(passed),
            "threshold": threshold,
            "confidence": confidence,
            "top": top,
            "second_score": second_score,
            "reason": reason,
        })

    conn.commit()
    conn.close()

    return {
        "ok": True,
        "race_id": race_id,
        "threshold": threshold,
        "threshold_mode": mode,
        "items": sorted(out_items, key=lambda x: x["race_no"])
    }


def get_race_decisions(race_id: str) -> Dict[str, Any]:
    init_decision_tables()

    conn = sqlite3.connect(_db())
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute("""
    SELECT *
    FROM race_ai_decisions
    WHERE race_id=?
    ORDER BY race_no ASC
    """, (race_id,)).fetchall()

    conn.close()

    return {
        "ok": True,
        "race_id": race_id,
        "items": [dict(r) for r in rows],
        "settings": get_threshold_settings()
    }
