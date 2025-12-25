from backend.db.conn import get_conn

def ensure_threshold_table():
    con = get_conn()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS kpi_threshold (
      id INTEGER PRIMARY KEY CHECK (id = 1),
      warn REAL NOT NULL,
      fail REAL NOT NULL
    )
    """)

    cur.execute("""
    INSERT OR IGNORE INTO kpi_threshold (id, warn, fail)
    VALUES (1, 0.55, 0.45)
    """)

    con.commit()
    con.close()
