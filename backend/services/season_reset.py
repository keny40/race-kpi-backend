import sqlite3
from datetime import datetime

DB_PATH = "races.db"

def _season_from_month(m: int) -> str:
    if m in (12, 1, 2):
        return "WINTER"
    if m in (3, 4, 5):
        return "SPRING"
    if m in (6, 7, 8):
        return "SUMMER"
    return "FALL"

def current_season() -> str:
    return _season_from_month(datetime.now().month)

def _get_setting(cur, k: str) -> str | None:
    cur.execute("SELECT v FROM app_settings WHERE k=? LIMIT 1", (k,))
    row = cur.fetchone()
    return row[0] if row else None

def _set_setting(cur, k: str, v: str):
    cur.execute("""
        INSERT INTO app_settings(k, v) VALUES(?, ?)
        ON CONFLICT(k) DO UPDATE SET v=excluded.v
    """, (k, v))

def check_and_reset_on_season_change() -> bool:
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    now_season = current_season()
    prev = _get_setting(cur, "season")

    if prev is None:
        _set_setting(cur, "season", now_season)
        con.commit()
        con.close()
        return False

    if prev == now_season:
        con.close()
        return False

    # 시즌 전환 감지 → 전략 상태 리셋
    now = datetime.now().isoformat()
    cur.execute("""
        UPDATE strategy_state
        SET enabled=1,
            weight_multiplier=1.0,
            last_score=0.0,
            last_updated_at=?
    """, (now,))

    _set_setting(cur, "season", now_season)

    con.commit()
    con.close()
    return True
