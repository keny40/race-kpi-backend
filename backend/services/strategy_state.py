from backend.services.admin_log import log_admin_action
from backend.services.slack_notifier import _post_webhook

_force_pass_enabled = False

def is_force_pass_enabled() -> bool:
    return _force_pass_enabled

def force_pass(reason: str = "MANUAL"):
    global _force_pass_enabled
    if _force_pass_enabled:
        return
    _force_pass_enabled = True
    log_admin_action("FORCE_PASS_ON", reason)
    _post_webhook(f"🚨 FORCE PASS ON\n사유: {reason}")

def force_pass_off():
    global _force_pass_enabled
    if not _force_pass_enabled:
        return
    _force_pass_enabled = False
    log_admin_action("FORCE_PASS_OFF", "AUTO_OR_MANUAL")
    _post_webhook("✅ KPI GREEN 복귀 → FORCE PASS OFF")
