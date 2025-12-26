# backend/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from backend.services.state_guard import get_system_state

scheduler = BackgroundScheduler()


def daily_summary_job():
    state = get_system_state()
    # Slack 연동은 B-5에서 연결
    print("[DAILY SUMMARY]", state)


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            daily_summary_job,
            "cron",
            hour=9,
            minute=0
        )
        scheduler.start()
