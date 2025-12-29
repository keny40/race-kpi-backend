# backend/services/admin_log.py

from datetime import datetime
from backend.services.slack_notifier import _post_webhook  # 내부 사용

# === 관리자 액션 로그 (메모리 기반) ===
_ADMIN_LOGS: list[dict] = []


def log_action(
    action: str,
    detail: str | None = None,
    actor: str = "admin",
):
    entry = {
        "action": action,
        "detail": detail,
        "actor": actor,
        "timestamp": datetime.utcnow().isoformat(),
    }

    _ADMIN_LOGS.append(entry)

    # Slack 알림 (실패해도 무시)
    try:
        _post_webhook(
            f"🛠 ADMIN ACTION\n"
            f"action={action}\n"
            f"detail={detail}\n"
            f"actor={actor}"
        )
    except Exception:
        pass


# === 🔹 legacy / admin 라우터 호환 alias ===
def log_admin_action(
    action: str,
    detail: str | None = None,
    actor: str = "admin",
):
    log_action(action=action, detail=detail, actor=actor)


def get_admin_logs(limit: int = 100) -> list[dict]:
    return _ADMIN_LOGS[-limit:]
