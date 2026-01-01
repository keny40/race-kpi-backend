# backend/services/strategy_state.py

_state = {
    "paused": False,
    "force_pass": False,
}

# ===== pause =====
def pause():
    _state["paused"] = True

def resume():
    _state["paused"] = False

def is_paused() -> bool:
    return _state["paused"]

# ===== force pass =====
def force_pass_on():
    _state["force_pass"] = True

def force_pass_off():
    _state["force_pass"] = False

def is_force_pass() -> bool:
    return _state["force_pass"]

# ===== get =====
def get_state():
    return {
        "paused": _state["paused"],
        "force_pass": _state["force_pass"],
    }
