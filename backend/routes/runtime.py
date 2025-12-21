from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

# === 설정 ===
MIN_SAMPLE = 30          # 최소 샘플 수
DROP_RATE = 0.45         # 폐기 기준 Hit Rate
LOCK_DURATION = 300      # lock 유지 시간(초)

PRESETS = {
    "A": {"active": True},
    "B": {"active": True}
}

RUNTIME = {
    "locked": False,
    "lock_until": None,
    "preset_stats": {
        "A": {"pred": 0, "hit": 0},
        "B": {"pred": 0, "hit": 0}
    },
    "preset_active": ["A", "B"],
    "updated_at": None
}

class PresetResult(BaseModel):
    preset: str
    hit: bool

@router.post("/runtime/preset-result")
def preset_result(r: PresetResult):
    st = RUNTIME["preset_stats"][r.preset]
    st["pred"] += 1
    if r.hit:
        st["hit"] += 1

    # === 자동 폐기 ===
    if st["pred"] >= MIN_SAMPLE:
        rate = st["hit"] / st["pred"]
        if rate < DROP_RATE and r.preset in RUNTIME["preset_active"]:
            RUNTIME["preset_active"].remove(r.preset)
            PRESETS[r.preset]["active"] = False

    RUNTIME["updated_at"] = datetime.utcnow().isoformat()
    return RUNTIME

@router.post("/runtime/lock")
def lock():
    RUNTIME["locked"] = True
    RUNTIME["lock_until"] = (datetime.utcnow().timestamp() + LOCK_DURATION)
    return RUNTIME

@router.post("/runtime/unlock")
def unlock():
    RUNTIME["locked"] = False
    RUNTIME["lock_until"] = None
    return RUNTIME

@router.get("/runtime/state")
def get_state():
    # lock 만료 자동 해제
    if RUNTIME["locked"] and datetime.utcnow().timestamp() > RUNTIME["lock_until"]:
        RUNTIME["locked"] = False
        RUNTIME["lock_until"] = None
    return RUNTIME
