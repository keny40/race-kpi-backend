from fastapi import APIRouter
from datetime import datetime
from backend.routes.meta import META
from backend.routes.runtime import RUNTIME

router = APIRouter()

FACTORY = {
    "min_pred": 60,
    "alpha_to_bias": 0.25,   # ewma가 0.5보다 높으면 +bias, 낮으면 -bias로 변환
    "max_abs_bias": 0.15,
    "default_miss_trigger": 3,
    "default_release_hit": 2,
    "generated": []          # 히스토리
}

def _clamp(x, lo, hi):
    return max(lo, min(hi, x))

def _pick_best_combo():
    best = None
    for k, v in META.get("combo", {}).items():
        if v.get("pred", 0) < int(FACTORY["min_pred"]):
            continue
        if best is None or float(v.get("ewma", 0.0)) > float(best["ewma"]):
            best = {"key": k, "ewma": float(v.get("ewma", 0.0)), "pred": int(v.get("pred", 0))}
    return best

@router.post("/preset/generate")
def generate(payload: dict = None):
    payload = payload or {}
    for k in ["min_pred","alpha_to_bias","max_abs_bias"]:
        if k in payload:
            FACTORY[k] = payload[k]

    best = _pick_best_combo()
    if not best:
        return {"ok": False, "why": "no_combo_meets_min_pred", "min_pred": FACTORY["min_pred"]}

    # ewma(0~1)를 bias(-max~+max)로 변환: (ewma-0.5)*alpha_to_bias
    raw = (best["ewma"] - 0.5) * float(FACTORY["alpha_to_bias"])
    bias = _clamp(raw, -float(FACTORY["max_abs_bias"]), float(FACTORY["max_abs_bias"]))

    # 프리셋 파라미터 구성(기본 + 메타 기반 조정)
    # ewma가 높을수록 release를 빠르게, miss_trigger는 조금 높게(공격)
    release_hit = 1 if best["ewma"] >= 0.58 else FACTORY["default_release_hit"]
    miss_trigger = 4 if best["ewma"] >= 0.58 else FACTORY["default_miss_trigger"]

    name = payload.get("name") or f"META_{datetime.utcnow().strftime('%Y%m%d_%H%M')}"

    preset = {
        "name": name,
        "source": best,
        "params": {
            "miss_trigger": miss_trigger,
            "release_hit": release_hit,
            "hit_bias": abs(bias),
            "miss_bias": -abs(bias)
        },
        "ts": datetime.utcnow().isoformat()
    }

    FACTORY["generated"].append(preset)
    if len(FACTORY["generated"]) > 200:
        FACTORY["generated"].pop(0)

    # 런타임에 “활성 프리셋”으로 등록(운영에 즉시 투입 가능)
    RUNTIME.setdefault("preset_active", [])
    if name not in RUNTIME["preset_active"]:
        RUNTIME["preset_active"].append(name)
    RUNTIME.setdefault("preset_stats", {})
    RUNTIME["preset_stats"].setdefault(name, {"pred": 0, "hit": 0})

    return {"ok": True, "preset": preset, "active_presets": RUNTIME["preset_active"]}

@router.get("/preset/factory")
def state():
    return {"factory": FACTORY, "meta_reco": META.get("recommendation")}
