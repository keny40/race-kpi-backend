# backend/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from backend.services.state_guard import get_system_state, notify_slack


def daily_summary():
    state = get_system_state()
    notify_slack(
        f"📊 Daily KPI Summary\n"
        f"Status: {state['status']}\n"
        f"Accuracy: {state['accuracy']}\n"
        f"HIT: {state['hit']} / MISS: {state['miss']}"
    )


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(daily_summary, "cron", hour=9, minute=0)
    scheduler.start()
