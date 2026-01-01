from typing import Dict, Tuple
from datetime import datetime

_SEASON = {
    "paused": False,
    "pause_reason": "",
    "paused_at": None,   # ISO string
}

class SeasonManager:
    @staticmethod
    def get_status() -> Dict:
        return dict(_SEASON)

    @staticmethod
    def pause(reason: str = "MANUAL"):
        _SEASON["paused"] = True
        _SEASON["pause_reason"] = reason or "MANUAL"
        _SEASON["paused_at"] = datetime.utcnow().isoformat()

    @staticmethod
    def resume():
        _SEASON["paused"] = False
        _SEASON["pause_reason"] = ""
        _SEASON["paused_at"] = None

    @staticmethod
    def require_not_paused() -> Tuple[bool, str]:
        if _SEASON.get("paused"):
            return False, _SEASON.get("pause_reason") or "PAUSED"
        return True, ""

    @staticmethod
    def paused_seconds() -> int:
        if not _SEASON.get("paused") or not _SEASON.get("paused_at"):
            return 0
        try:
            t0 = datetime.fromisoformat(_SEASON["paused_at"])
            return int((datetime.utcnow() - t0).total_seconds())
        except Exception:
            return 0
