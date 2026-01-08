from apscheduler.schedulers.background import BackgroundScheduler
import requests

def start_daily():
    sched = BackgroundScheduler()
    sched.add_job(
        lambda: requests.post("http://localhost:8000/api/today/run"),
        trigger="cron",
        hour=9, minute=30
    )
    sched.start()
