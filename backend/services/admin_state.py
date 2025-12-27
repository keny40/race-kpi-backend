from backend.db.conn import get_conn
from datetime import datetime


def set_state(key: str, enabled: bool):
    con = get_conn()
    cur = con.cursor()

    cur.execute("""
        UPDATE strategy_state
        SET enabled = ?, updated_at = ?
        WHERE strategy = ?
    """, (
        1 if enabled else 0,
        datetime.utcnow().isoformat(),
        key
    ))

    con.commit()
    con.close()


def get_state(key: str) -> bool:
    con = get_conn()
    cur = con.cursor()

    cur.execute("""
        SELECT enabled
        FROM strategy_state
        WHERE strategy = ?
    """, (key,))

    row = cur.fetchone()
    con.close()

    if not row:
        return False
    return bool(row[0])
