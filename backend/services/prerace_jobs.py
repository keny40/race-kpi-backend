# backend/services/prerace_jobs.py
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from backend.services.db import DB_PATH
from backend.services.settings_store import get_setting

def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_tables():
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS prerace_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            race_id TEXT NOT NULL UNIQUE,
            run_at TEXT NOT NULL,              -- ISO datetime
            status TEXT NOT NULL DEFAULT 'PENDING', -- PENDING/RUNNING/DONE/FAIL
            last_error TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")

def _parse_race_datetime(race_date: str, start_time: str) -> Optional[datetime]:
    # race_date: YYYY-MM-DD, start_time: HH:MM (or HH:MM:SS)
    try:
        if len(start_time.strip()) == 5:
            dt_str = f"{race_date} {start_time}:00"
        else:
            dt_str = f"{race_date} {start_time}"
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

def schedule_jobs_for_races(race_ids: List[str]) -> Dict[str, Any]:
    """
    race_ids에 대해 races 테이블에서 race_date/start_time 조회 후
    (출발 n분 전) prerace_jobs에 upsert
    """
    ensure_tables()
    before_min = int(get_setting("AUTO_PRERACE_BEFORE_MIN", "10") or "10")

    conn = _conn()
    cur = conn.cursor()

    inserted = 0
    skipped = 0
    errors: List[str] = []

    for race_id in race_ids:
        row = cur.execute("""
            SELECT race_date, start_time
            FROM races
            WHERE race_id=?
        """, (race_id,)).fetchone()

        if not row:
            skipped += 1
            continue

        race_date = (row["race_date"] or "").strip()
        start_time = (row["start_time"] or "").strip()
        dt = _parse_race_datetime(race_date, start_time)
        if dt is None:
            errors.append(f"{race_id}: invalid race_date/start_time ({race_date} / {start_time})")
            continue

        run_at = (dt - timedelta(minutes=before_min)).isoformat(timespec="seconds")
        now = _now_iso()

        try:
            cur.execute("""
                INSERT INTO prerace_jobs(race_id, run_at, status, created_at, updated_at)
                VALUES(?, ?, 'PENDING', ?, ?)
                ON CONFLICT(race_id) DO UPDATE SET
                    run_at=excluded.run_at,
                    status=CASE
                        WHEN prerace_jobs.status IN ('DONE','RUNNING') THEN prerace_jobs.status
                        ELSE 'PENDING'
                    END,
                    updated_at=excluded.updated_at
            """, (race_id, run_at, now, now))
            inserted += 1
        except Exception as e:
            errors.append(f"{race_id}: {e}")

    conn.commit()
    conn.close()

    return {
        "ok": len(errors) == 0,
        "scheduled": inserted,
        "skipped": skipped,
        "errors": errors,
        "before_min": before_min,
    }

def pick_due_jobs(limit: int = 20) -> List[sqlite3.Row]:
    ensure_tables()
    conn = _conn()
    cur = conn.cursor()
    now = _now_iso()
    rows = cur.execute("""
        SELECT *
        FROM prerace_jobs
        WHERE status='PENDING'
          AND run_at <= ?
        ORDER BY run_at ASC
        LIMIT ?
    """, (now, limit)).fetchall()
    conn.close()
    return rows

def mark_running(job_id: int) -> None:
    ensure_tables()
    conn = _conn()
    cur = conn.cursor()
    now = _now_iso()
    cur.execute("""
        UPDATE prerace_jobs
        SET status='RUNNING', updated_at=?
        WHERE id=?
    """, (now, job_id))
    conn.commit()
    conn.close()

def mark_done(job_id: int) -> None:
    ensure_tables()
    conn = _conn()
    cur = conn.cursor()
    now = _now_iso()
    cur.execute("""
        UPDATE prerace_jobs
        SET status='DONE', last_error=NULL, updated_at=?
        WHERE id=?
    """, (now, job_id))
    conn.commit()
    conn.close()

def mark_fail(job_id: int, err: str) -> None:
    ensure_tables()
    conn = _conn()
    cur = conn.cursor()
    now = _now_iso()
    cur.execute("""
        UPDATE prerace_jobs
        SET status='FAIL', last_error=?, updated_at=?
        WHERE id=?
    """, (err[:2000], now, job_id))
    conn.commit()
    conn.close()

def reset_fail_to_pending(race_id: str) -> None:
    ensure_tables()
    conn = _conn()
    cur = conn.cursor()
    now = _now_iso()
    cur.execute("""
        UPDATE prerace_jobs
        SET status='PENDING', last_error=NULL, updated_at=?
        WHERE race_id=?
    """, (now, race_id))
    conn.commit()
    conn.close()
