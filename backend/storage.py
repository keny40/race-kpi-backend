import sqlite3
from datetime import datetime, timedelta
from typing import Dict

DB_PATH = "backend/races.db"


def _connect():
    return sqlite3.connect(DB_PATH)


# ① 예측 결과 저장 (사전)
def save_prediction(
    race_id: str,
    strategy: str,
    predicted_horse: int,
    confidence: float,
    decision: str,
):
    con = _connect()
    cur = con.cursor()
    cur.execute(
        """
        INSERT INTO predictions
        (race_id, strategy, predicted_horse, confidence, decision, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            race_id,
            strategy,
            predicted_horse,
            confidence,
            decision,
            datetime.utcnow(),
        ),
    )
    con.commit()
    con.close()


# ② 실경기 결과 저장 (사후)
def save_result(
    race_id: str,
    winner_horse: int,
    payoff: float,
):
    con = _connect()
    cur = con.cursor()
    cur.execute(
        """
        INSERT OR REPLACE INTO results
        (race_id, winner_horse, payoff, finished_at)
        VALUES (?, ?, ?, ?)
        """,
        (race_id, winner_horse, payoff, datetime.utcnow()),
    )
    con.commit()
    con.close()


# ③ KPI 요약 (실데이터)
def fetch_kpi_summary(days: int) -> Dict:
    since = datetime.utcnow() - timedelta(days=days)

    con = _connect()
    cur = con.cursor()

    cur.execute(
        """
        SELECT p.decision, p.predicted_horse, r.winner_horse
        FROM predictions p
        LEFT JOIN results r ON p.race_id = r.race_id
        WHERE p.created_at >= ?
        """,
        (since,),
    )

    rows = cur.fetchall()
    con.close()

    total = len(rows)
    if total == 0:
        return {"days": days, "roi": 0.0, "hit_rate": 0.0, "pass_rate": 1.0}

    win = 0
    lose = 0
    pass_cnt = 0

    for decision, pred, winner in rows:
        if decision == "PASS":
            pass_cnt += 1
        elif winner is None:
            continue
        elif pred == winner:
            win += 1
        else:
            lose += 1

    bet_cnt = win + lose
    roi = (win - lose) / bet_cnt if bet_cnt > 0 else 0.0
    hit_rate = win / bet_cnt if bet_cnt > 0 else 0.0
    pass_rate = pass_cnt / total

    return {
        "days": days,
        "roi": round(roi, 4),
        "hit_rate": round(hit_rate, 4),
        "pass_rate": round(pass_rate, 4),
    }
