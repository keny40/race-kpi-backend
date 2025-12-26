# backend/scheduler.py

from backend.routes.kpi_report import report_pdf
from backend.services.state_guard import get_system_state
from backend.services.slack_notify import send_slack_message


def daily_summary_job():
    state = get_system_state()
    send_slack_message(f"[DAILY KPI] Current system state: {state}")
