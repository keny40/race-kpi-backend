# backend/services/admin_log.py

from datetime import datetime
from backend.services.slack_notifier import _post_webhook  # 내부 알림용 (선택)

# === 관리자 액션 로그 (프로세스 메모리 기준) ===
_ADMIN_LOGS: list[dict] = []


def log_action(
    action: str,
    detail: str | None = None,
    actor: str = "admin",
):
    """
    관리자 액션 기록
    - action: FORCE_PASS_ON / FORCE_PASS_OFF / PAUSE / RESUME 등
    - detail: 추가 설명
    - actor: 수행 주체
    """

    entry = {
        "action": action,
        "detail": detail,
        "actor": actor,
        "timestamp": datetime.utcnow().isoformat(),
    }

    _ADMIN_LOGS.append(entry)

    # 필요 시 Slack에도 남김 (선택)
    try:
        _post_webhook(
            f"🛠 ADMIN ACTION\n"
            f"action={action}\n"
            f"detail={detail}\n"
            f"actor={actor}"
        )
    except Exception:
        pass


def get_admin_logs(limit: int = 100) -> list[dict]:
    return _ADMIN_LOGS[-limit:]
