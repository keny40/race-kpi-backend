# backend/services/strategy_state.py

from datetime import datetime
from backend.services.slack_notifier import send_red_alert

# === FORCE PASS 상태 (프로세스 전역) ===
_FORCE_PASS_ENABLED = False
_FORCE_PASS_REASON = None
_FORCE_PASS_AT = None


# === 상태 조회 (predict.py에서 사용) ===
def is_force_pass_enabled() -> bool:
    return _FORCE_PASS_ENABLED


def get_force_pass_status() -> dict:
    return {
        "enabled": _FORCE_PASS_ENABLED,
        "reason": _FORCE_PASS_REASON,
        "since": _FORCE_PASS_AT,
    }


# === 상태 변경 ===
def enable_force_pass(reason: str, payload: dict | None = None):
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
