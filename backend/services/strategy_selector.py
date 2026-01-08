from __future__ import annotations
from typing import List, Dict, Any, Optional
import math


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _sigmoid(z: float) -> float:
    if z >= 0:
        e = math.exp(-z)
        return 1.0 / (1.0 + e)
    e = math.exp(z)
    return e / (1.0 + e)


def score_candidate(
    calibrated_conf: float,
    roi: float,
    bets: int,
    warn_roi: float = 0.05,
    promote_roi: float = 0.30,
) -> float:
    """
    운영용 점수
    1) 확률(=calibrated_conf) 우선
    2) ROI는 가중치로만 반영(데이터 적을수록 영향 축소)
    """
    c = _clip(float(calibrated_conf), 0.0, 1.0)

    # ROI 영향은 warmup 구간에서는 약하게
    n = max(0, int(bets))
    w = _clip(n / 50.0, 0.0, 1.0)  # bets>=50부터 ROI 영향 100%

    # ROI를 -1~+1을 대략 -1~+1로 압축
    roi_adj = _clip(float(roi), -1.0, 1.0)

    # ROI가 warn 이하이면 감점, promote 이상이면 가점
    roi_bonus = 0.0
    if roi_adj <= warn_roi:
        roi_bonus = -0.15 * w
    if roi_adj >= promote_roi:
        roi_bonus = +0.15 * w

    # 최종 점수
    return c + roi_bonus


def pick_best_strategy(candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    candidates item 예시
    {
      "strategy": "BASE",
      "predicted_horse_no": 3,
      "confidence": 0.72,
      "calibrated_confidence": 0.72,
      "roi": 0.12,
      "bets": 40
    }
    """
    if not candidates:
        return None

    best = None
    best_score = -1e9

    for x in candidates:
        cconf = x.get("calibrated_confidence")
        if cconf is None:
            cconf = x.get("confidence", 0.0)

        s = score_candidate(
            calibrated_conf=float(cconf),
            roi=float(x.get("roi", 0.0)),
            bets=int(x.get("bets", 0)),
        )
        if s > best_score:
            best_score = s
            best = dict(x)
            best["score"] = float(s)

    return best
