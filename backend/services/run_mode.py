# backend/services/run_mode.py

from threading import Lock

_MODE = "DRY_RUN"
_lock = Lock()

def get_mode():
    return _MODE

def is_live():
    return _MODE == "LIVE"

def set_mode(mode: str):
    global _MODE
    if mode not in ("DRY_RUN", "LIVE"):
        raise ValueError("invalid mode")

    with _lock:
        _MODE = mode
        return _MODE
