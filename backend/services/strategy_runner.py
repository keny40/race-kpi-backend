# backend/services/strategy_runner.py
from typing import List, Dict, Any
from backend.services.strategy_state import is_enabled, auto_switch

STRATEGIES = ["BASE", "RECENCY", "MARKOV"]


def run_strategies(race_id: str, options: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    auto_switch(STRATEGIES)
    candidates: List[Dict[str, Any]] = []

    if is_enabled("BASE"):
        candidates.append({
            "horse_no": 1, "strategy": "BASE",
            "confidence": 0.30, "calibrated_confidence": 0.28, "roi": 1.05
        })

    if is_enabled("RECENCY"):
        candidates.append({
            "horse_no": 3, "strategy": "RECENCY",
            "confidence": 0.42, "calibrated_confidence": 0.38, "roi": 1.20
        })

    if is_enabled("MARKOV"):
        candidates.append({
            "horse_no": 5, "strategy": "MARKOV",
            "confidence": 0.35, "calibrated_confidence": 0.32, "roi": 1.10
        })

    return candidates
