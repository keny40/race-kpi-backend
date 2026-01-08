# backend/services/auto_tuner.py
import sqlite3
import time
from typing import Dict

DB_PATH = "races.db"

# 튜닝 파라미터
EMA_ALPHA = 0.25
WINDOW = 80
WEIGHT_CLAMP = (0.8, 1.25)
PASS_CLAMP = (0.18, 0.35)
COOLDOWN_SEC = 300

_last_tune_ts = 0


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ema(values):
    if not values:
        return None
    ema = values[0]
    for v in values[1:]:
        ema = EMA_ALPHA * v + (1 - EMA_ALPHA) * ema
    return ema


def compute_strategy_score(strategy: str) -> Dict[str, float]:
    """
    전략별 최근 성과 요약
    """
    conn = _conn()
    cur = conn.cursor()
    rows = cur.execute(
        """
        SELECT
          CASE WHEN decision = winner THEN 1.0 ELSE 0.0 END AS hit,
          COALESCE(roi, 1.0) AS roi
        FROM predictions p
        LEFT JOIN actual_results a ON p.race_id = a.race_id
        WHERE p.strategy = ?
        ORDER BY p.created_at DESC
        LIMIT ?
        """,
        (strategy, WINDOW),
    ).fetchall()
    conn.close()

    if not rows:
        return {"hit_ema": 0.5, "roi_ema": 1.0}

    hit_ema = _ema([float(r["hit"]) for r in rows]) or 0.5
    roi_ema = _ema([float(r["roi"]) for r in rows]) or 1.0
    return {"hit_ema": hit_ema, "roi_ema": roi_ema}


def tune_weights(current_weights: Dict[str, float]) -> Dict[str, float]:
    global _last_tune_ts
    now = time.time()
    if now - _last_tune_ts < COOLDOWN_SEC:
        return current_weights

    new_weights = {}
    for strat, w in current_weights.items():
        s = compute_strategy_score(strat)
        factor = (0.6 * s["hit_ema"]) + (0.4 * min(1.2, s["roi_ema"]))
        nw = max(WEIGHT_CLAMP[0], min(WEIGHT_CLAMP[1], round(w * factor, 3)))
        new_weights[strat] = nw

    _last_tune_ts = now
    return new_weights


def tune_pass_threshold(base_threshold: float) -> float:
    """
    최근 전체 성과로 PASS 임계값 조정
    성과 나쁠수록 threshold ↑ (보수)
    """
    conn = _conn()
    cur = conn.cursor()
    rows = cur.execute(
        """
        SELECT CASE WHEN p.decision = a.winner THEN 1.0 ELSE 0.0 END AS hit
        FROM predictions p
        JOIN actual_results a ON p.race_id = a.race_id
        ORDER BY p.created_at DESC
        LIMIT ?
        """,
        (WINDOW,),
    ).fetchall()
    conn.close()

    if not rows:
        return base_threshold

    hit_ema = _ema([float(r["hit"]) for r in rows]) or 0.5
    # hit 낮으면 threshold 상향
    adj = (0.5 - hit_ema) * 0.1
    tuned = base_threshold + adj
    return max(PASS_CLAMP[0], min(PASS_CLAMP[1], round(tuned, 3)))
