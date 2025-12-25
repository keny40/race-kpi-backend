import sqlite3

con = sqlite3.connect("races.db")
cur = con.cursor()

cur.execute("PRAGMA table_info(predictions)")
rows = cur.fetchall()

for r in rows:
    print(r)

con.close()
