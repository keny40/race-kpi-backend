from apscheduler.schedulers.background import BackgroundScheduler
import requests
import os

SCHEDULE_HOUR = int(os.getenv("KPI_NOTIFY_HOUR", "23"))
SCHEDULE_MIN = int(os.getenv("KPI_NOTIFY_MIN", "0"))

def start_scheduler():
    scheduler = BackgroundScheduler(timezone="Asia/Seoul")

    scheduler.add_job(
        func=run_kpi_notify,
        trigger="cron",
        hour=SCHEDULE_HOUR,
        minute=SCHEDULE_MIN,
        id="daily_kpi_notify",
        replace_existing=True
    )

    scheduler.start()

def run_kpi_notify():
    try:
        requests.post("http://127.0.0.1:8000/api/kpi/notify", timeout=10)
    except Exception as e:
        print("[SCHEDULER ERROR]", e)
