import sqlite3

DB_PATH = "races.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

race_id = "R20251219_01"

for horse_no in range(1, 11):
    cur.execute("""
    INSERT OR IGNORE INTO entries (race_id, gate)
    VALUES (?, ?)
    """, (race_id, horse_no))

conn.commit()
conn.close()

print("entries seed completed")
