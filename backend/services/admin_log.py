import sqlite3
from datetime import datetime

DB_PATH = "races.db"


def log_admin_action(action: str, reason: str = ""):
    """
    관리자 액션 로그 기록
    """
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_action_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            reason TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        INSERT INTO admin_action_log (action, reason, created_at)
        VALUES (?, ?, ?)
        """,
        (action, reason, datetime.utcnow().isoformat()),
    )

    con.commit()
    con.close()
