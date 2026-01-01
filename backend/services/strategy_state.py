# backend/services/strategy_state.py
from datetime import datetime

# =====================================================
# 전역 운영 상태 (Single Source of Truth)
# =====================================================

_STATE = {
    "run_mode": "ACTIVE",     # ACTIVE | PAUSED
    "paused": False,
    "force_pass": False,
    "updated_at": datetime.utcnow().isoformat()
}

# =====================================================
# READ
# =====================================================

def get_run_mode_status():
    return {
        "run_mode": _STATE["run_mode"],
        "paused": _STATE["paused"],
        "force_pass": _STATE["force_pass"],
        "updated_at": _STATE["updated_at"]
    }

def is_paused() -> bool:
    return _STATE["paused"]

def is_force_pass_enabled() -> bool:
    return _STATE["force_pass"]

# =====================================================
# WRITE (표준 API)
# =====================================================

def set_run_mode_active():
    _STATE["run_mode"] = "ACTIVE"
    _STATE["paused"] = False
    _STATE["updated_at"] = datetime.utcnow().isoformat()
    return get_run_mode_status()

def set_run_mode_paused():
    _STATE["run_mode"] = "PAUSED"
    _STATE["paused"] = True
    _STATE["updated_at"] = datetime.utcnow().isoformat()
    return get_run_mode_status()

def set_force_pass(enabled: bool):
    _STATE["force_pass"] = enabled
    _STATE["updated_at"] = datetime.utcnow().isoformat()
    return get_run_mode_status()

# =====================================================
# 🔥 호환용 ALIAS (중요)
# 기존 코드에서 어떤 이름을 써도 안 깨지게
# =====================================================

def enable_force_pass():
    return set_force_pass(True)

def disable_force_pass():
    return set_force_pass(False)
