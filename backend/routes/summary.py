from fastapi import APIRouter
import sqlite3
from datetime import date

DB_PATH = "races.db"
router = APIRouter(prefix="/api", tags=["summary"])

def _conn():
    conn = sqlite3.connect(DB_PATH)
    return conn

@router.get("/summary")
def summary():
    conn = _conn()
    cur = conn.cursor()

    total_preds = cur.execute("SELECT COUNT(*) FROM predictions").fetchone()[0] or 0
    passed = cur.execute("SELECT COUNT(*) FROM predictions WHERE decision='PASS'").fetchone()[0] or 0

    joined = cur.execute(
        """
        SELECT
          SUM(CASE WHEN p.decision = r.winner THEN 1 ELSE 0 END) AS hit,
          SUM(CASE WHEN p.decision != 'PASS' AND p.decision != r.winner THEN 1 ELSE 0 END) AS miss
        FROM predictions p
        JOIN results r ON p.race_id = r.race_id
        """
    ).fetchone()
    hit = joined[0] or 0
    miss = joined[1] or 0

    net_pl = cur.execute(
        """
        SELECT
          SUM(CASE WHEN p.decision = r.winner THEN r.payoff ELSE -1 END)
        FROM predictions p
        JOIN results r ON p.race_id = r.race_id
        WHERE p.decision != 'PASS'
        """
    ).fetchone()[0] or 0.0

    conn.close()
    return {
        "date": date.today().isoformat(),
        "total_predictions": total_preds,
        "hit": hit,
        "miss": miss,
        "pass": passed,
        "net_pl": round(float(net_pl), 2),
    }
