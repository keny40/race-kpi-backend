from datetime import datetime, timedelta
from backend.services.rpt_data_source import list_races, get_race_detail
from backend.services.predict_runner import run_predict_for_race
from backend.services.predict_config import PREDICT_CONFIG

def check_and_repredict(now=None):
    if not PREDICT_CONFIG["enable_prestart_repredict"]:
        return

    now = now or datetime.now()

    for r in list_races():
        if not r.get("start_time"):
            continue

        start = datetime.strptime(
            f'{r["race_date"]} {r["start_time"]}', "%Y-%m-%d %H:%M"
        )
        delta = (start - now).total_seconds() / 60

        if 0 < delta <= PREDICT_CONFIG["minutes_before_start"]:
            detail = get_race_detail(r["race_id"]) or {}
            pred = detail.get("predict")

            if not pred or pred.get("decision") == "PASS":
                run_predict_for_race(r["race_id"])
