from fastapi import APIRouter
import sqlite3

router = APIRouter(prefix="/api/kpi", tags=["kpi"])

DB_PATH = "races.db"


@router.get("/strategy")
def kpi_by_strategy():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT p.strategy,
               COUNT(*) AS cnt,
               AVG(CASE WHEN p.decision = a.winner THEN 1 ELSE 0 END) AS hit,
               AVG(COALESCE(p.roi, 1)) AS roi
        FROM predictions p
        JOIN actual_results a ON p.race_id = a.race_id
        GROUP BY p.strategy
    """).fetchall()

    conn.close()

    return [
        {
            "strategy": r[0],
            "count": r[1],
            "hit": round(r[2], 3),
            "roi": round(r[3], 3),
        }
        for r in rows
    ]


@router.get("/user")
def kpi_by_user():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT p.user_id,
               COUNT(*) AS cnt,
               AVG(CASE WHEN p.decision = a.winner THEN 1 ELSE 0 END) AS hit,
               AVG(COALESCE(p.roi, 1)) AS roi
        FROM predictions p
        JOIN actual_results a ON p.race_id = a.race_id
        GROUP BY p.user_id
    """).fetchall()

    conn.close()

    return [
        {
            "user": r[0],
            "count": r[1],
            "hit": round(r[2], 3),
            "roi": round(r[3], 3),
        }
        for r in rows
    ]
