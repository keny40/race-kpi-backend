# backend/services/risk_guard.py
from typing import Optional, Dict, Any
from backend.services.db import get_conn

# ====== State ======
_PAUSED = False

# ====== Tunables (env로 빼도 됨) ======
MIN_SAMPLE = 10          # 최소 표본
WINDOW = 50              # 평가 구간(최근 N)
EV_PAUSE_TH = -0.05      # EV가 이보다 낮으면 위험
HIT_PAUSE_TH = 0.45      # BET hit rate가 이보다 낮으면 위험
MISS_STREAK_N = 5        # MISS 연속 N이면 즉시 중단

def is_paused() -> bool:
    return _PAUSED

def pause(reason: str):
    global _PAUSED
    _PAUSED = True
    print(f"[AUTO_PAUSE] {reason}")

def resume():
    global _PAUSED
    _PAUSED = False
    print("[RESUME] manual/auto resume")


def evaluate_all_and_maybe_pause():
    """
    혼합 로직:
    1) MISS 연속 N이면 즉시 중단
    2) 표본 >= MIN_SAMPLE 일 때만 EV+HIT 혼합 판단
       - (EV < EV_PAUSE_TH) AND (HIT_RATE < HIT_PAUSE_TH) → 중단
    """
    conn = get_conn()
    cur = conn.cursor()

    # 1) MISS streak
    streak = cur.execute("""
        SELECT hit_miss
        FROM pre_race_run_history
        ORDER BY run_at DESC
        LIMIT ?
    """, (MISS_STREAK_N,)).fetchall()

    if len(streak) == MISS_STREAK_N and all((r["hit_miss"] == "MISS") for r in streak):
        pause(f"MISS_STREAK_{MISS_STREAK_N}")
        return

    # 2) EV + HIT (odds 있는 표본만)
    row = cur.execute("""
    WITH recent AS (
      SELECT *
      FROM pre_race_run_history
      WHERE odds IS NOT NULL
      ORDER BY run_at DESC
      LIMIT ?
    )
    SELECT
      COUNT(*) AS sample_size,
      SUM(CASE WHEN bet_pass='BET' THEN 1 ELSE 0 END) AS bet_count,
      ROUND(
        SUM(CASE WHEN bet_pass='BET' AND hit_miss='HIT' THEN 1 ELSE 0 END) * 1.0 /
        NULLIF(SUM(CASE WHEN bet_pass='BET' THEN 1 ELSE 0 END), 0), 3
      ) AS hit_rate,
      ROUND(
        SUM(CASE WHEN bet_pass='BET' AND hit_miss='HIT' THEN odds ELSE 0 END) * 1.0 /
        NULLIF(SUM(CASE WHEN bet_pass='BET' THEN 1 ELSE 0 END), 0)
        - 1, 3
      ) AS ev
    FROM recent;
    """, (WINDOW,)).fetchone()

    sample_size = row["sample_size"] or 0
    bet_count = row["bet_count"] or 0
    hit_rate = row["hit_rate"]
    ev = row["ev"]

    if sample_size < MIN_SAMPLE or bet_count < MIN_SAMPLE or ev is None or hit_rate is None:
        return

    if ev < EV_PAUSE_TH and hit_rate < HIT_PAUSE_TH:
        pause(f"EV_HIT_GUARD ev={ev} hit={hit_rate} window={WINDOW}")
        return
