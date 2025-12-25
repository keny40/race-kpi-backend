from backend.db.conn import get_conn

def ensure_strategy_state():
    con = get_conn()
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS strategy_state (
      strategy TEXT PRIMARY KEY,
      enabled INTEGER NOT NULL DEFAULT 1,
      fail_streak INTEGER NOT NULL DEFAULT 0
    )
    """)
    con.commit()
    con.close()
