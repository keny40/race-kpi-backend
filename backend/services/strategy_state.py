from backend.db.conn import get_conn


def is_force_pass_enabled() -> bool:
    con = get_conn()
    cur = con.cursor()

    cur.execute("""
        SELECT enabled
        FROM strategy_state
        WHERE strategy = 'FORCE_PASS'
    """)

    row = cur.fetchone()
    con.close()

    if not row:
        return False
    return bool(row[0])
