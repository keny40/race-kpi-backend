from statistics import mean
from typing import Dict, Any

from backend import storage


def detect_anomaly(year: int, month: int) -> Dict[str, Any]:
    preds = storage.list_predictions_for_month(year, month)
    results = storage.list_results_for_month(year, month)

    hits = sum(1 for r in results if r["outcome"] == "HIT")
    misses = sum(1 for r in results if r["outcome"] == "MISS")
    passes = sum(1 for r in results if r["outcome"] == "PASS")

    total = hits + misses
    accuracy = hits / total if total > 0 else 0.0
    pass_rate = passes / max(1, len(results))

    confidences = [p["confidence"] for p in preds if p.get("confidence") is not None]
    avg_conf = mean(confidences) if confidences else 0.0

    alerts = []

    if accuracy < 0.45:
        alerts.append("Accuracy 급락")

    if pass_rate >= 0.30:
        alerts.append("PASS 비율 급증")

    if avg_conf < 0.25:
        alerts.append("Confidence 붕괴")

    return {
        "accuracy": round(accuracy, 4),
        "pass_rate": round(pass_rate, 4),
        "avg_confidence": round(avg_conf, 4),
        "alerts": alerts,
        "is_anomaly": len(alerts) > 0,
    }
