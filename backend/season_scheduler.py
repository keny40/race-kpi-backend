from apscheduler.triggers.interval import IntervalTrigger
from season import SeasonManager

def register_season_jobs(scheduler):
    scheduler.add_job(
        func=SeasonManager.evaluate_lock_state,
        trigger=IntervalTrigger(minutes=1),
        id="season_lock_guard",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
