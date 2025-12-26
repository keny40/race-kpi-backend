# backend/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from backend.routes.kpi_alert import check_and_alert


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        check_and_alert,
        trigger="cron",
        hour=9,
        minute=0
    )
    scheduler.start()
