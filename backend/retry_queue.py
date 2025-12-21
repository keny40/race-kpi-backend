import time
from typing import Optional
from backend import storage


MAX_RETRY = 5
RETRY_INTERVAL_SEC = 60


def enqueue(kind: str, payload: dict, last_error: str = ""):
    storage.enqueue_retry(kind, payload, last_error)


def process_queue_once():
    jobs = storage.fetch_retry_jobs(limit=5)
    for job in jobs:
        try:
            yield job
            storage.mark_retry_success(job["id"])
        except Exception as e:
            storage.mark_retry_failure(job["id"], str(e))


def loop_processor(handler):
    while True:
        for job in process_queue_once():
            handler(job)
        time.sleep(RETRY_INTERVAL_SEC)
