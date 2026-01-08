from fastapi import APIRouter
from backend.services.db import get_conn

router = APIRouter(prefix="/api/kpi", tags=["kpi"])

@router.get("/ev")
def get_ev():
    conn = get_conn()
    cur = conn.cursor()

    # odds 컬럼 존재 여부
    cols = [r["name"] for r in cur.execute(
        "PRAGMA table_info(pre_race_run_history)"
    ).fetchall()]

    if "odds" not in cols:
        return {"ev": None, "sample_size": 0, "reason": "odds_column_missing"}

    rows = cur.execute(
        """
        SELECT odds, hit_miss
        FROM pre_race_run_history
        WHERE bet_pass='BET'
          AND odds IS NOT NULL
        """
    ).fetchall()

    n = len(rows)
    if n < 5:
        return {"ev": None, "sample_size": n, "reason": "insufficient_samples"}

    hit = sum(1 for r in rows if r["hit_miss"] == "HIT")
    hit_rate = hit / n
    avg_odds = sum(r["odds"] for r in rows) / n

    ev = round(hit_rate * avg_odds - 1, 3)

    return {
        "ev": ev,
        "sample_size": n,
        "hit_rate": round(hit_rate, 3),
        "avg_odds": round(avg_odds, 3),
    }
