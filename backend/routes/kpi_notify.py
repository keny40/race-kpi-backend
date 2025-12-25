from fastapi import APIRouter
from datetime import datetime
import os
from backend.db.conn import get_conn
from backend.services.notify import send_slack_text, send_slack_file, send_mail
from backend.routes.kpi_report import build_kpi_pdf, REPORT_DIR

router = APIRouter(prefix="/api/kpi", tags=["kpi"])
FAIL_STREAK_LIMIT = int(os.getenv("FAIL_STREAK_LIMIT","3"))

def load_threshold(con):
    cur = con.cursor()
    cur.execute("SELECT warn, fail FROM kpi_threshold WHERE id=1")
    r = cur.fetchone()
    return (r[0], r[1]) if r else (0.55, 0.45)

@router.post("/notify")
def notify_kpi():
    con = get_conn()
    warn, fail = load_threshold(con)
    cur = con.cursor()

    # 전략별 결과 집계
    cur.execute("""
      SELECT strategy,
             SUM(CASE WHEN result='HIT' THEN 1 ELSE 0 END) hit,
             SUM(CASE WHEN result='MISS' THEN 1 ELSE 0 END) miss
      FROM v_race_match_strategy
      GROUP BY strategy
    """)
    rows = cur.fetchall()

    disabled = []
    for s, h, m in rows:
        acc = (h/(h+m)) if (h+m)>0 else 0.0
        cur.execute("INSERT OR IGNORE INTO strategy_state(strategy) VALUES(?)",(s,))
        if acc <= fail:
            cur.execute("UPDATE strategy_state SET fail_streak=fail_streak+1 WHERE strategy=?",(s,))
        else:
            cur.execute("UPDATE strategy_state SET fail_streak=0 WHERE strategy=?",(s,))
        cur.execute("SELECT fail_streak FROM strategy_state WHERE strategy=?",(s,))
        streak = cur.fetchone()[0]
        if streak >= FAIL_STREAK_LIMIT:
            cur.execute("UPDATE strategy_state SET enabled=0 WHERE strategy=?",(s,))
            disabled.append(s)

    con.commit()
    con.close()

    # PDF + 알림
    now = datetime.now()
    pdf = os.path.join(REPORT_DIR, f"latest_exec_{now:%Y%m%d_%H%M}.pdf")
    build_kpi_pdf(pdf)
    msg = f"[AUTO] Disabled strategies: {disabled}" if disabled else "[AUTO] All strategies OK"
    send_slack_text(msg)
    send_slack_file(msg, pdf)
    send_mail("[KPI AUTO]", msg, pdf)
    return {"disabled": disabled}
