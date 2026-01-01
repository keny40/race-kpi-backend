from fastapi import APIRouter, Query, HTTPException
from backend.services.replay_loader import load_replay_data
from backend.services.season import SeasonManager
from backend.services.risk_guard import evaluate_and_maybe_pause

router = APIRouter(prefix="/api/replay", tags=["replay"])

@router.post("/run")
def run_replay(
    mode: str = Query("MOCK", pattern="^(MOCK|REAL)$"),
    date: str | None = Query(None)
):
    ok, reason = SeasonManager.require_not_paused()
    if not ok:
        raise HTTPException(status_code=423, detail=f"paused: {reason}")

    races = load_replay_data(mode=mode, date=date)
    results = []

    for r in races:
        # 실제 feature는 이후 REAL feature로 교체하면 됨
        features = {
            "volatility": 0.6,
            "disagreement": 0.5,
            "data_quality": 0.9 if mode == "REAL" else 0.3
        }

        risk = evaluate_and_maybe_pause(
            race_id=r["race_id"],
            features=features,
            meta={"mode": mode, "horses": len(r.get("horses") or [])},
            mode=mode,
            season_pause_cb=SeasonManager.pause
        )

        results.append({
            "race_id": r["race_id"],
            "horses": r.get("horses") or [],
            "risk": risk
        })

    return {
        "mode": mode,
        "count": len(results),
        "results": results,
        "season": SeasonManager.get_status()
    }
