# backend/services/ops_scheduler.py
from datetime import datetime
from backend.services.db import get_conn
from backend.services.odds_provider import get_odds_for_race
from backend.services.risk_guard import evaluate_all_and_maybe_pause

def run_once(race_id: str):
    conn = get_conn()
    cur = conn.cursor()

    # ===== 예측 결과(여기는 기존 예측 로직으로 교체) =====
    decision = 5
    confidence = 0.72
    bet_pass = "BET"
    hit_miss = "HIT"
    confidence_bucket = "0.7-0.8"
    rule_snapshot = '{"threshold":0.65}'

    # ===== odds (PDF) =====
    odds_res = get_odds_for_race(race_id, decision)
    odds = odds_res.odds  # 신뢰도 낮으면 None

    # rule_snapshot에 odds 메타를 같이 남김(스키마 변경 없이 추적 가능)
    rule_snapshot = (
        rule_snapshot[:-1]
        + f', "odds_source":"{odds_res.source}", "odds_conf":{odds_res.confidence:.2f}, "odds_reason":"{odds_res.reason}"'
        + "}"
    )

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cur.execute("""
        INSERT INTO pre_race_run_history (
            race_id, ran_at, run_at,
            confidence, decision, bet_pass, hit_miss,
            rule_snapshot, confidence_bucket, odds
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        race_id, now, now,
        confidence, str(decision), bet_pass, hit_miss,
        rule_snapshot, confidence_bucket, odds
    ))

    conn.commit()

    # ===== EV + HIT RATE 혼합 중단 =====
    evaluate_all_and_maybe_pause()

    return {
        "status": "ok",
        "race_id": race_id,
        "decision": decision,
        "confidence": confidence,
        "odds": odds,
        "odds_confidence": odds_res.confidence,
        "odds_reason": odds_res.reason,
    }
