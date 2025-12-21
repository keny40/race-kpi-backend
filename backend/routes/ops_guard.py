from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

GUARD = {
    "enabled": True,
    "stopped": False,
    "stop_reason": None,
    "window": 30,
    "min_pred": 15,
    "stop_rate_below": 0.35,
    "stop_miss_streak": 5,
    "events": []
}

RECENT = []  # [{"hit":bool,"ts":...}]

def push_feedback(hit: bool):
    RECENT.append({"hit": bool(hit), "ts": datetime.utcnow().isoformat()})
    if len(RECENT) > int(GUARD["window"]):
        RECENT.pop(0)

def calc():
    n = len(RECENT)
    if n == 0:
        return {"n": 0, "rate": 0.0, "miss_streak": 0}
    hit = sum(1 for x in RECENT if x["hit"])
    rate = hit / n
    ms = 0
    for x in reversed(RECENT):
        if x["hit"]:
            break
        ms += 1
    return {"n": n, "rate": rate, "miss_streak": ms}

def check_and_maybe_stop():
    if not GUARD["enabled"] or GUARD["stopped"]:
        return {"action": "none", "calc": calc()}
    c = calc()
    if c["n"] < int(GUARD["min_pred"]):
        return {"action": "none", "why": "insufficient_samples", "calc": c}

    triggered = (c["miss_streak"] >= int(GUARD["stop_miss_streak"])) or (c["rate"] < float(GUARD["stop_rate_below"]))
    if triggered:
        GUARD["stopped"] = True
        GUARD["stop_reason"] = {"ts": datetime.utcnow().isoformat(), "calc": c, "thresholds": {
            "stop_rate_below": GUARD["stop_rate_below"],
            "stop_miss_streak": GUARD["stop_miss_streak"],
            "window": GUARD["window"],
            "min_pred": GUARD["min_pred"]
        }}
        GUARD["events"].append({"ts": GUARD["stop_reason"]["ts"], "event": "STOP", "detail": GUARD["stop_reason"]})
        if len(GUARD["events"]) > 300:
            GUARD["events"].pop(0)
        return {"action": "stop", "calc": c}
    return {"action": "none", "why": "safe", "calc": c}

@router.get("/ops/guard")
def state():
    return {"guard": GUARD, "recent": RECENT, "calc": calc()}

@router.post("/ops/guard")
def configure(payload: dict):
    for k in ["enabled","window","min_pred","stop_rate_below","stop_miss_streak"]:
        if k in payload:
            GUARD[k] = payload[k]
    return {"ok": True, "guard": GUARD}

@router.post("/ops/stop")
def manual_stop(payload: dict = None):
    GUARD["stopped"] = True
    GUARD["stop_reason"] = payload or {"ts": datetime.utcnow().isoformat(), "manual": True}
    GUARD["events"].append({"ts": datetime.utcnow().isoformat(), "event": "MANUAL_STOP", "detail": GUARD["stop_reason"]})
    return {"ok": True, "guard": GUARD}

@router.post("/ops/resume")
def resume():
    GUARD["stopped"] = False
    GUARD["stop_reason"] = None
    GUARD["events"].append({"ts": datetime.utcnow().isoformat(), "event": "RESUME"})
    return {"ok": True, "guard": GUARD}
