# backend/routes/races.py
from fastapi import APIRouter
import sqlite3

router = APIRouter()

@router.get("/races")
def get_races():
    conn = sqlite3.connect("backend/races.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM races")
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "race_id": r[0],
            "name": r[1],
            "date": r[2],
            "location": r[3]
        })

    return result
