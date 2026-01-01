# backend/services/ops_scheduler.py
import threading
import time

from backend.services.mock_race_data import generate_mock_race
from backend.services.strategy_state import is_paused, is_force_pass
from backend.services.log_store import insert_log

_scheduler = {
    "running": False,
    "thread": None,
    "interval_sec": 30,
}

def run_once():
    race = generate_mock_race()

    insert_log(
        action="MOCK_RUN",
        level="INFO",
        detail={
            "race_id": race["race_id"],
            "track": race["track"],
            "race_no": race["race_no"],
            "winner": race["winner"],
            "force_pass": is_force_pass(),
        },
    )

def _loop():
    while _scheduler["running"]:
        if is_paused():
            time.sleep(_scheduler["interval_sec"])
            continue

        run_once()
        time.sleep(_scheduler["interval_sec"])

def start_scheduler():
    if _scheduler["running"]:
        return

    _scheduler["running"] = True
    _scheduler["thread"] = threading.Thread(target=_loop, daemon=True)
    _scheduler["thread"].start()

    insert_log(action="SCHEDULER_START", level="INFO")

def stop_scheduler():
    _scheduler["running"] = False
    insert_log(action="SCHEDULER_STOP", level="INFO")
