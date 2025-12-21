from fastapi import APIRouter
import sqlite3

router = APIRouter()
DB_PATH = "races.db"

@router.get("/retry/status")
def retry_status():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) FROM retry_queue")
    total = cur.fetchone()[0]

    cur.execute("SELECT AVG(retry_count) FROM retry_queue")
    avg_retry = cur.fetchone()[0] or 0

    cur.execute("""
        SELECT last_error, COUNT(*) 
        FROM retry_queue 
        GROUP BY last_error 
        ORDER BY COUNT(*) DESC 
        LIMIT 5
    """)
    errors = [{"error": e, "count": c} for e, c in cur.fetchall()]

    cur.execute("""
        SELECT rc_date, meet, rc_no, retry_count, updated_at
        FROM retry_queue
        ORDER BY updated_at DESC
        LIMIT 20
    """)
    pending = [
        {
            "rc_date": r[0],
            "meet": r[1],
            "rc_no": r[2],
            "retry": r[3],
            "updated_at": r[4],
        }
        for r in cur.fetchall()
    ]

    con.close()

    return {
        "total": total,
        "avg_retry": round(avg_retry, 2),
        "top_errors": errors,
        "pending": pending,
    }
