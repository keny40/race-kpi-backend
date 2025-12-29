# backend/services/strategy_state.py

from datetime import datetime
from backend.services.slack_notifier import send_red_alert

# === FORCE PASS 상태 (전역 단일 소스) ===
_FORCE_PASS_ENABLED = False
_FORCE_PASS_REASON = None
_FORCE_PASS_AT = None


# === 상태 조회 ===
def is_force_pass_enabled() -> bool:
    return _FORCE_PASS_ENABLED


def get_force_pass_status() -> dict:
    return {
        "enabled": _FORCE_PASS_ENABLED,
        "reason": _FORCE_PASS_REASON,
        "since": _FORCE_PASS_AT,
    }


# === 내부 구현 (정식 API) ===
def enable_force_pass(reason: str = "MANUAL", payload: dict | None = None):
    global _FORCE_PASS_ENABLED, _FORCE_PASS_REASON, _FORCE_PASS_AT

    _FORCE_PASS_ENABLED = True
    _FORCE_PASS_REASON = reason
    _FORCE_PASS_AT = datetime.utcnow().isoformat()

    if payload:
        send_red_alert(payload)


def disable_force_pass():
    global _FORCE_PASS_ENABLED, _FORCE_PASS_REASON, _FORCE_PASS_AT

    _FORCE_PASS_ENABLED = False
    _FORCE_PASS_REASON = None
    _FORCE_PASS_AT = None


# === 🔹 admin / legacy 호환용 alias ===
def force_pass(reason: str = "MANUAL"):
    enable_force_pass(reason=reason)


def force_pass_off():
    disable_force_pass()
