# backend/services/meta_selector.py
import sqlite3
import math
from typing import Dict, Any, List, Tuple

DB_PATH = "races.db"

def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _softmax(xs: List[float]) -> List[float]:
    m = max(xs) if xs else 0.0
    exps = [math.exp(x - m) for x in xs]
    s = sum(exps) or 1.0
    return [e / s for e in exps]

def get_strategy_weight_map() -> Dict[str, float]:
    """
    strategy_weights 테이블 기반 (없으면 1.0)
    """
    m: Dict[str, float] = {}
    conn = _conn()
    cur = conn.cursor()
    try:
        rows = cur.execute("SELECT strategy, weight FROM strategy_weights").fetchall()
        for r in rows:
            m[str(r["strategy"])] = float(r["weight"])
    except Exception:
        pass
    conn.close()
    return m

def recent_perf(minutes: int = 180) -> Dict[str, Dict[str, float]]:
    """
    최근 성과(전략별 hit rate + 평균 roi) 계산
    predictions에 strategy, decision(or predicted_horse_no), roi 저장되어 있다고 가정
    actual_results에 winner 있다고 가정
    """
    conn = _conn()
    cur = conn.cursor()
    perf: Dict[str, Dict[str, float]] = {}

    rows = cur.execute(f"""
        SELECT
          p.strategy AS strategy,
          COUNT(*) AS n,
          AVG(CASE WHEN CAST(p.predicted_horse_no AS TEXT)=CAST(a.winner AS TEXT) THEN 1 ELSE 0 END) AS hit,
          AVG(COALESCE(p.roi, 0)) AS roi
        FROM predictions p
        JOIN actual_results a ON p.race_id=a.race_id
        WHERE p.passed=0
          AND p.predicted_horse_no IS NOT NULL
          AND p.created_at >= datetime('now','-{int(minutes)} minutes')
        GROUP BY p.strategy
    """).fetchall()

    for r in rows:
        s = str(r["strategy"])
        perf[s] = {
            "n": float(r["n"] or 0),
            "hit": float(r["hit"] or 0),
            "roi": float(r["roi"] or 0),
        }

    conn.close()
    return perf

def score_candidate(candidate: Dict[str, Any], w_map: Dict[str, float], perf_map: Dict[str, Dict[str, float]]) -> float:
    """
    후보 점수 = calibrated_confidence * 전략가중치 * (성과 보정)
    """
    s = str(candidate.get("strategy") or candidate.get("name") or "")
    p = float(candidate.get("calibrated_confidence", candidate.get("confidence", 0.0)) or 0.0)
    roi = float(candidate.get("roi", 0.0) or 0.0)
    base_w = float(w_map.get(s, 1.0))

    perf = perf_map.get(s)
    perf_boost = 1.0
    if perf and perf.get("n", 0) >= 10:
        perf_boost *= (0.7 + 0.6 * float(perf.get("hit", 0.0)))     # hit 반영
        perf_boost *= (1.0 + 0.5 * max(0.0, float(perf.get("roi", 0.0))))  # roi 반영(양수만)

    # 너무 공격적이지 않게
    return (p * 0.8 + max(0.0, roi) * 0.2) * base_w * perf_boost

def pick_best(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    w_map = get_strategy_weight_map()
    perf_map = recent_perf()

    scored: List[Tuple[float, Dict[str, Any]]] = []
    for c in candidates:
        scored.append((score_candidate(c, w_map, perf_map), c))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1] if scored else {}
