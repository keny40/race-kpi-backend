from collections import deque

# 최근 confidence 저장
_recent_conf = deque(maxlen=5)

# 기준값 (운영 튜닝값)
WARN_THRESHOLD = 0.58
PAUSE_THRESHOLD = 0.48
RESUME_THRESHOLD = 0.60


def update_confidence(confidence: float):
    """
    pre-race 실행 후 confidence 누적
    """
    try:
        _recent_conf.append(float(confidence))
    except Exception:
        pass


def avg_confidence() -> float:
    if not _recent_conf:
        return 1.0
    return sum(_recent_conf) / len(_recent_conf)


def risk_level() -> str:
    """
    NORMAL / WARN / PAUSE
    """
    avg = avg_confidence()

    if avg < PAUSE_THRESHOLD:
        return "PAUSE"
    if avg < WARN_THRESHOLD:
        return "WARN"
    return "NORMAL"


def should_auto_resume() -> bool:
    """
    PAUSE 상태에서 자동 재개 가능 여부
    """
    avg = avg_confidence()
    return avg >= RESUME_THRESHOLD
