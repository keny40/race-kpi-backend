# backend/services/health_watch.py
import time
import threading
import requests

from backend.services.slack_notify import send_text

_state = {
    "ok": True
}

def _notify_down(reason: str):
    if _state["ok"]:
        send_text(f"❗ HEALTH DOWN\n- reason: {reason}")
    _state["ok"] = False

def _notify_up():
    if not _state["ok"]:
        send_text("✅ HEALTH RECOVERED")
    _state["ok"] = True

def start_watch(url: str, interval_sec: int = 10):
    def loop():
        while True:
            try:
                r = requests.get(url, timeout=3)
                if r.status_code == 200:
                    _notify_up()
                else:
                    _notify_down(f"status={r.status_code}")
            except Exception as e:
                _notify_down(str(e))
            time.sleep(interval_sec)

    t = threading.Thread(target=loop, daemon=True)
    t.start()
