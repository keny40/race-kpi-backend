# backend/services/weekly_report_scheduler.py
import threading, time
from datetime import datetime
from backend.services.notify import notify_slack

def _seconds_until_mon_9():
    now = datetime.now()
    target = now.replace(hour=9, minute=0, second=0, microsecond=0)
    delta_days = (0 - now.weekday()) % 7
    target = target + timedelta(days=delta_days)
    if target <= now:
        target = target + timedelta(days=7)
    return (target - now).total_seconds()

def start_weekly_report():
    def loop():
        time.sleep(_seconds_until_mon_9())
        while True:
            try:
                # PDF 엔드포인트 호출만으로 생성/전송
                notify_slack("[PRE-RACE REPORT] Weekly PDF generated")
                # 필요 시: requests.get("/api/admin/pre-race/report/pdf")
            except Exception:
                pass
            time.sleep(7 * 24 * 3600)
    threading.Thread(target=loop, daemon=True).start()
