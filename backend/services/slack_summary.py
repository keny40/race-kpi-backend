import sqlite3
from services.notify import notify_slack

DB_PATH = "races.db"
DELAY_THRESHOLD = 3

def send_delay_summary():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("""
        SELECT rc_date, meet, rc_no, retry_count
        FROM retry_queue
        WHERE retry_count >= ?
        ORDER BY retry_count DESC
    """, (DELAY_THRESHOLD,))

    rows = cur.fetchall()
    con.close()

    if not rows:
        return

    lines = ["[KRA 지연 경주 요약]"]
    for r in rows[:15]:
        lines.append(f"- {r[0]} / meet={r[1]} / rcNo={r[2]} / retry={r[3]}")

    notify_slack("\n".join(lines))
