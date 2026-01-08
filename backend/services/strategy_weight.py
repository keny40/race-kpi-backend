# backend/services/strategy_weight.py
from typing import Dict
from backend.services.auto_tuner import tune_weights

_WEIGHTS: Dict[str, float] = {
    "BASE": 1.00,
    "RECENCY": 1.10,
    "MARKOV": 1.05,
    "KNN": 1.00,
    "MOMENTUM": 1.10,
    "MINORITY": 0.95,
}

def get_weight(strategy_name: str) -> float:
    return _WEIGHTS.get(strategy_name.upper(), 1.0)

def auto_tune():
    global _WEIGHTS
    _WEIGHTS = tune_weights(_WEIGHTS)
