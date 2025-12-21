import sqlite3

conn = sqlite3.connect("races.db")
tables = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table';"
).fetchall()
conn.close()

print(tables)
