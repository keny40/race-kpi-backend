from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

RISK = {
    "enabled": True,
    "window": 20,          # 최근 N회
    "min_pred": 12,        # 최소 피드백 수
    "unlock_rate_below": 0.40,  # 최근N hitrate가 이 값 미만이면 unlock
    "unlock_miss_streak": 4,    # 연속 실패가 이 값 이상이면 unlock
    "events": []           # 로그
}

# 최근 피드백 버퍼: [{"hit":bool,"ts":...}]
RECENT = []

def push_feedback(hit: bool):
    RECENT.append({"hit": bool(hit), "ts": datetime.utcnow().isoformat()})
    if len(RECENT) > int(RISK["window"]):
        RECENT.pop(0)

def _calc():
    n = len(RECENT)
    if n == 0:
        return {"n": 0, "rate": 0.0, "miss_streak": 0}
    hit = sum(1 for x in RECENT if x["hit"])
    rate = hit / n
    # miss streak from tail
    ms = 0
    for x in reversed(RECENT):
        if x["hit"]:
            break
        ms += 1
    return {"n": n, "rate": rate, "miss_streak": ms}

@router.get("/runtime/risk")
def get_risk():
    return {"risk": RISK, "recent": RECENT, "calc": _calc()}

@router.post("/runtime/risk")
def set_risk(payload: dict):
    # enabled/window/min_pred/unlock_rate_below/unlock_miss_streak
    for k in ["enabled","window","min_pred","unlock_rate_below","unlock_miss_streak"]:
        if k in payload:
            RISK[k] = payload[k]
    return {"ok": True, "risk": RISK}

@router.post("/runtime/risk-check")
def risk_check(runtime_state: dict):
    """
    runtime_state는 호출 측에서 넘겨줌 (순환 임포트 방지)
    예: {"locked":true, "fixed_combo":..., ...}
    """
    if not RISK["enabled"]:
        return {"ok": True, "action": "none", "why": "disabled", "calc": _calc()}

    calc = _calc()
    if not runtime_state.get("locked", False):
        return {"ok": True, "action": "none", "why": "not_locked", "calc": calc}

    if calc["n"] < int(RISK["min_pred"]):
        return {"ok": True, "action": "none", "why": "insufficient_samples", "calc": calc}

    if calc["miss_streak"] >= int(RISK["unlock_miss_streak"]) or calc["rate"] < float(RISK["unlock_rate_below"]):
        evt = {
            "ts": datetime.utcnow().isoformat(),
            "action": "unlock",
            "why": {
                "n": calc["n"],
                "rate": calc["rate"],
                "miss_streak": calc["miss_streak"],
                "thresholds": {
                    "unlock_rate_below": RISK["unlock_rate_below"],
                    "unlock_miss_streak": RISK["unlock_miss_streak"]
                }
            }
        }
        RISK["events"].append(evt)
        if len(RISK["events"]) > 200:
            RISK["events"].pop(0)
        return {"ok": True, "action": "unlock", "event": evt, "calc": calc}

    return {"ok": True, "action": "none", "why": "safe", "calc": calc}
