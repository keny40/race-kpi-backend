from fastapi import APIRouter
from backend.services.db import get_conn
import sqlite3

router = APIRouter(prefix="/api/kpi", tags=["kpi"])


@router.get("/ev")
def get_ev():
    """
    EV 계산:
    - bet_pass = 'BET'
    - odds IS NOT NULL
    - hit_miss 기준으로 HIT / MISS 계산
    """

    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 실제 테이블 컬럼 확인 (디버그 및 안전장치)
    cols = {
        row["name"]
        for row in cur.execute("PRAGMA table_info(pre_race_run_history);").fetchall()
    }

    required_cols = {"bet_pass", "odds", "hit_miss"}
    if not required_cols.issubset(cols):
        return {
            "ev": None,
            "sample_size": 0,
            "reason": f"missing_columns:{sorted(required_cols - cols)}",
        }

    rows = cur.execute(
        """
        SELECT odds, hit_miss
        FROM pre_race_run_history
        WHERE bet_pass = 'BET'
          AND odds IS NOT NULL
        """
    ).fetchall()

    if not rows:
        return {
            "ev": None,
            "sample_size": 0,
            "reason": "no_valid_samples",
        }

    total = 0.0
    for r in rows:
        odds = float(r["odds"])
        hit = str(r["hit_miss"]).upper() == "HIT"

        # 적중 시 (odds - 1), 실패 시 -1
        total += (odds - 1.0) if hit else -1.0

    ev = total / len(rows)

    return {
        "ev": round(ev, 4),
        "sample_size": len(rows),
    }
