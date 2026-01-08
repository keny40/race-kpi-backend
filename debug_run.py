from backend.services.strategy_selector import pick_best_strategy
from backend.services.kpi_service import get_roi_by_strategy
from backend.services.prediction_store import upsert_prediction

race_id = "TEST_RACE_FINAL"
strategy_names = ["BASE"]

cands = []

for s in strategy_names:
    pred_horse_no = 3
    conf = 0.72
    cal_conf = conf

    roi_row = get_roi_by_strategy(s)

    cands.append({
        "strategy": s,
        "predicted_horse_no": pred_horse_no,
        "confidence": conf,
        "calibrated_confidence": cal_conf,
        "roi": roi_row["roi"],
        "bets": roi_row["bets"],
    })

best = pick_best_strategy(cands)

for x in cands:
    is_best = (best is not None and x["strategy"] == best["strategy"])
    stake = 1000.0 if is_best else 0.0
    passed = 0 if is_best else 1

    upsert_prediction(
        race_id=race_id,
        strategy=x["strategy"],
        predicted_horse_no=x["predicted_horse_no"],
        confidence=x["confidence"],
        calibrated_confidence=x["calibrated_confidence"],
        passed=passed,
        stake=stake,
        meta={"score": (best["score"] if is_best else None)}
    )

print("DONE:", best)
