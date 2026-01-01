# backend/services/risk_guard.py
import threading

from backend.services.log_store import insert_log
from backend.services.slack_notify import send_red_alert, send_reset_notice

# =========================
# Risk settings / state
# =========================
_lock = threading.Lock()

_settings = {
    "red_threshold": 0.85,     # 점수 기준 예시
    "red_streak_pause": 3,     # 연속 RED N회면 pause
}

_state = {
    "paused": False,
    "red_streak": 0,
    "last": {
        "score": 0.0,
        "is_red": False,
        "reasons": {},
    }
}


def get_risk_settings():
    with _lock:
        return dict(_settings)


def is_paused():
    with _lock:
        return bool(_state["paused"])


def reset_red_streak():
    with _lock:
        before = {"paused": _state["paused"], "red_streak": _state["red_streak"]}
        _state["red_streak"] = 0
        _state["paused"] = False
        after = {"paused": _state["paused"], "red_streak": _state["red_streak"]}

    insert_log("RESET", {"before": before, "after": after})
    send_reset_notice(before, after)
    return {"before": before, "after": after}


def evaluate_and_maybe_pause(score: float, reasons: dict):
    """
    return:
      {
        score, is_red, streak, paused, reasons
      }
    """
    with _lock:
        red = float(score) >= float(_settings["red_threshold"])
        if red:
            _state["red_streak"] += 1
        else:
            _state["red_streak"] = 0

        if _state["red_streak"] >= int(_settings["red_streak_pause"]):
            _state["paused"] = True

        _state["last"] = {"score": float(score), "is_red": red, "reasons": reasons or {}}

        out = {
            "score": float(score),
            "is_red": bool(red),
            "streak": int(_state["red_streak"]),
            "paused": bool(_state["paused"]),
            "reasons": reasons or {},
        }

    # 로그 + 슬랙은 lock 밖에서
    insert_log("RUN", out)
    if out["is_red"]:
        send_red_alert(out["score"], out["streak"], out["paused"], out["reasons"])
    return out
