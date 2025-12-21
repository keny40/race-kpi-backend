from __future__ import annotations
from typing import Dict, Any, List
from statistics import mean

from backend import storage


def dashboard_monthly(year: int, month: int) -> Dict[str, Any]:
    preds = storage.list_predictions_for_month(year, month)
    results = storage.list_results_for_month(year, month)

    hits = sum(1 for r in results if r.get("outcome") == "HIT")
    misses = sum(1 for r in results if r.get("outcome") == "MISS")
    passes = sum(1 for r in results if r.get("outcome") == "PASS")
    total = hits + misses
    acc = round(hits / total, 4) if total > 0 else 0.0

    confidences = [float(p["confidence"]) for p in preds if p.get("confidence") is not None]
    avg_conf = round(mean(confidences), 4) if confidences else 0.0

    # confidence 구간 분포 (간단 4-bin)
    bins = {"<0.25": 0, "0.25-0.4": 0, "0.4-0.6": 0, ">=0.6": 0}
    for c in confidences:
        if c < 0.25:
            bins["<0.25"] += 1
        elif c < 0.4:
            bins["0.25-0.4"] += 1
        elif c < 0.6:
            bins["0.4-0.6"] += 1
        else:
            bins[">=0.6"] += 1

    return {
        "period": f"{year:04d}-{month:02d}",
        "accuracy": acc,
        "hits": hits,
        "misses": misses,
        "passes": passes,
        "avg_confidence": avg_conf,
        "confidence_bins": bins,
        "pred_count": len(preds),
        "result_count": len(results),
    }


def dashboard_season(season_key: str) -> Dict[str, Any]:
    m = storage.season_metrics(season_key)
    preds = storage.list_predictions_for_season(season_key)
    conf = [float(p["confidence"]) for p in preds if p.get("confidence") is not None]
    avg_conf = round(mean(conf), 4) if conf else 0.0

    return {
        **m,
        "avg_confidence": avg_conf,
        "pred_count": len(preds),
    }
