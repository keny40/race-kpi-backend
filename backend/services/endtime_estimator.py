import sqlite3
from datetime import datetime
from statistics import mean

DB_PATH = "races.db"

def _hhmm_from_iso(iso_str: str) -> int | None:
    try:
        dt = datetime.fromisoformat(iso_str)
        return int(dt.strftime("%H%M"))
    except Exception:
        return None

def _season_from_month(month: int) -> str:
    if month in (12, 1, 2):
        return "WINTER"
    if month in (3, 4, 5):
        return "SPRING"
    if month in (6, 7, 8):
        return "SUMMER"
    return "FALL"

def estimate_expected_end_hhmm(
    rc_date: str,
    meet: int,
    rc_no: int,
    fallback: str = "2359"
) -> str:
    """
    우선순위:
    1) meet+rc_no+weekday+season
    2) meet+rc_no
    3) fallback
    """
    dt = datetime.strptime(rc_date, "%Y%m%d")
    weekday = dt.weekday()          # 0=Mon
    season = _season_from_month(dt.month)

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    def _avg_hhmm(query, params):
        cur.execute(query, params)
        rows = cur.fetchall()
        hhmm = [_hhmm_from_iso(r[0]) for r in rows if _hhmm_from_iso(r[0]) is not None]
        return int(round(mean(hhmm))) if hhmm else None

    # 1️⃣ meet+rc_no+weekday+season
    avg = _avg_hhmm(
        """
        SELECT confirmed_at
        FROM ingest_meta
        WHERE meet=? AND rc_no=? AND weekday=? AND season=?
          AND confirmed_at IS NOT NULL
        ORDER BY confirmed_at DESC
        LIMIT 30
        """,
        (meet, rc_no, weekday, season)
    )

    # 2️⃣ meet+rc_no
    if avg is None:
        avg = _avg_hhmm(
            """
            SELECT confirmed_at
            FROM ingest_meta
            WHERE meet=? AND rc_no=? AND confirmed_at IS NOT NULL
            ORDER BY confirmed_at DESC
            LIMIT 30
            """,
            (meet, rc_no)
        )

    con.close()

    if avg is None:
        return fallback

    return f"{avg:04d}"
