# backend/services/score_aggregator.py
from typing import Dict, Any, List
from backend.services.strategy_weight import get_weight, auto_tune
from backend.services.recent_roi import get_recent_roi_factor
from backend.services.auto_tuner import tune_pass_threshold

BASE_PASS_THRESHOLD = 0.25
LOW_CONF_PASS = 0.18
LOW_ROI_PASS = 0.95


def compute_score(candidate: Dict[str, Any]) -> Dict[str, Any]:
    strategy = candidate.get("strategy", "BASE")
    weight = get_weight(strategy)
    conf = float(candidate.get("calibrated_confidence", 0))
    roi = float(candidate.get("roi", 1.0))
    recent_factor = get_recent_roi_factor(strategy)

    final_score = conf * roi * weight * recent_factor

    return {
        **candidate,
        "strategy_weight": weight,
        "recent_roi_factor": recent_factor,
        "final_score": round(final_score, 6),
    }


def choose_best(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not candidates:
        return {"decision": "PASS", "reason": "no_candidates"}

    # 🔁 자동 튜닝 (쿨다운 포함)
    auto_tune()
    pass_threshold = tune_pass_threshold(BASE_PASS_THRESHOLD)

    scored = [compute_score(c) for c in candidates]
    best = max(scored, key=lambda x: x["final_score"])

    if (
        best.get("calibrated_confidence", 0) < LOW_CONF_PASS
        or best.get("roi", 1.0) < LOW_ROI_PASS
        or best["final_score"] < pass_threshold
    ):
        return {
            "decision": "PASS",
            "reason": "auto_tuned_pass",
            "pass_threshold": pass_threshold,
            "best_candidate": best,
            "all_candidates": scored,
        }

    return {
        "decision": best.get("horse_no"),
        "pass_threshold": pass_threshold,
        "best_candidate": best,
        "all_candidates": scored,
    }
