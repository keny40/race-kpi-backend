from fastapi import APIRouter
import sqlite3

DB_PATH = "/tmp/races.db"

router = APIRouter(prefix="/api/kpi", tags=["kpi"])

@router.get("/summary")
def get_kpi_summary():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN p.decision = a.winner THEN 1 ELSE 0 END) as hit,
            SUM(CASE WHEN p.decision != a.winner THEN 1 ELSE 0 END) as miss
        FROM predictions p
        JOIN race_actuals a
          ON p.race_id = a.race_id
    """)

    row = cur.fetchone()
    con.close()

    total = row[0] or 0
    hit = row[1] or 0
    miss = row[2] or 0

    accuracy = round(hit / total, 4) if total > 0 else 0.0

    return {
        "total": total,
        "hit": hit,
        "miss": miss,
        "accuracy": accuracy
    }
