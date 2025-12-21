from fastapi import APIRouter
from datetime import datetime
from backend.routes.runtime import RUNTIME
from backend.routes.optimizer import MATRIX

router = APIRouter()

SEASONS = []

LOCK_POLICY = {
    "unlock_on_commit": True,
    "keep_if_rate_above": 0.55
}

def _calc_summary():
    rates = []
    for v in MATRIX.values():
        if v["pred"] >= 20:
            rates.append(v["hit"] / v["pred"])
    avg_rate = sum(rates) / len(rates) if rates else 0.0

    best = None
    best_rate = 0
    for (m, p), v in MATRIX.items():
        if v["pred"] < 20:
            continue
        r = v["hit"] / v["pred"]
        if r > best_rate:
            best_rate = r
            best = {"model": m, "preset": p, "rate": r}

    return {
        "avg_combo_rate_20plus": avg_rate,
        "best_combo": best,
        "locked": RUNTIME.get("locked", False)
    }

def commit_season(payload: dict):
    summary = _calc_summary()

    season = {
        "ts": datetime.utcnow().isoformat(),
        "reason": payload.get("reason"),
        "summary": summary,
        "runtime_snapshot": RUNTIME.copy(),
        "matrix_size": len(MATRIX)
    }
    SEASONS.append(season)

    # === LOCK 정책 ===
    if LOCK_POLICY["unlock_on_commit"]:
        if summary["avg_combo_rate_20plus"] < LOCK_POLICY["keep_if_rate_above"]:
            RUNTIME["locked"] = False
            RUNTIME["fixed_combo"] = None

    # === 초기화 ===
    MATRIX.clear()
    RUNTIME["preset_stats"] = {
        k: {"pred": 0, "hit": 0} for k in RUNTIME["preset_stats"]
    }
    RUNTIME["preset_active"] = ["A", "B"]

    return {
        "report": {
            "summary": summary,
            "season_ts": season["ts"]
        }
    }

@router.get("/season/log")
def season_log():
    return {"items": SEASONS}
