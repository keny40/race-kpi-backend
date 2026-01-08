# backend/services/alert_guard.py
from datetime import datetime, timedelta

_last_sent = {}

def can_send(key: str, cooldown_min=30) -> bool:
    now = datetime.utcnow()
    last = _last_sent.get(key)
    if last and now - last < timedelta(minutes=cooldown_min):
        return False
    _last_sent[key] = now
    return True
