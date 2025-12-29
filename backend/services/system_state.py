# backend/services/system_state.py
from datetime import datetime

_SYSTEM_STATE = {
    "mode": "RUNNING",
    "updated_at": None,
}

def get_state() -> dict:
    return {
        "mode": _SYSTEM_STATE["mode"],
        "updated_at": _SYSTEM_STATE["updated_at"],
    }

def set_state(mode: str):
    if mode not in ("RUNNING", "PAUSED", "STOPPED"):
        raise ValueError("invalid system state")
    _SYSTEM_STATE["mode"] = mode
    _SYSTEM_STATE["updated_at"] = datetime.utcnow().isoformat()
