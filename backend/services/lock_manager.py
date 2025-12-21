import sqlite3
from datetime import datetime, timedelta
from typing import Optional

from backend.routes.kpi_report import generate_kpi_report_pdf_bytes
from backend.services.lock_notifier import notify_lock_with_pdf


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_tables(con):
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS system_lock (
            id INTEGER PRIMARY KEY CHECK (id=1),
            locked INTEGER,
            reason TEXT,
            updated_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lock_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            reason TEXT,
            created_at TEXT
        )
    """)
    cur.execute("INSERT OR IGNORE INTO system_lock VALUES (1,0,'','')")
    con.commit()


def lock_and_notify(
    *,
    con,
    reason,
    period_for_pdf,
    pdf_pages,
    lock_level,
    window,
    details=None
):
    ensure_tables(con)
    cur = con.cursor()

    cur.execute("""
        UPDATE system_lock
        SET locked=1, reason=?, updated_at=?
        WHERE id=1
    """, (reason, _now()))
    con.commit()

    cur.execute("""
        INSERT INTO lock_history(level, reason, created_at)
        VALUES (?, ?, ?)
    """, (lock_level, reason, _now()))
    con.commit()

    try:
        pdf_bytes = generate_kpi_report_pdf_bytes(
            period=period_for_pdf,
            summary_pages=pdf_pages,
            include_chart=True
        )
    except Exception:
        pdf_bytes = None

    try:
        notify_lock_with_pdf(
            pdf_bytes=pdf_bytes,
            lock_reason=reason,
            lock_level=lock_level,
            window=window,
            details=details,
        )
    except Exception:
        pass


def unlock_if_expired(con, cooldown_minutes: int):
    cur = con.cursor()
    cur.execute("SELECT locked, updated_at FROM system_lock WHERE id=1")
    locked, ts = cur.fetchone()

    if not locked or not ts:
        return

    locked_at = datetime.fromisoformat(ts)
    if datetime.now() - locked_at >= timedelta(minutes=cooldown_minutes):
        cur.execute("""
            UPDATE system_lock
            SET locked=0, reason='AUTO UNLOCK', updated_at=?
            WHERE id=1
        """, (_now(),))
        con.commit()
