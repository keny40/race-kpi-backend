import sqlite3
from collections import defaultdict
from math import exp

DB_PATH = "races.db"

# -----------------------------
# 설정값 (튜닝 포인트)
# -----------------------------
LOOKBACK_RACES = 3      # 최근 N경주
PASS_THRESHOLD = 0.55   # 이 값 미만이면 PASS
ODDS_FLOOR = 1.01       # 배당 최소값
TEMP = 1.5              # softmax temperature (낮을수록 공격적)

# -----------------------------
# 유틸
# -----------------------------
def softmax(scores, temp=1.0):
    exps = [exp(s / temp) for s in scores]
    s = sum(exps)
    return [e / s for e in exps] if s > 0 else [0 for _ in scores]

# -----------------------------
# 데이터 로드
# -----------------------------
def load_recent_races(con, lookback):
    cur = con.cursor()
    cur.execute("""
        SELECT DISTINCT race_id
        FROM races
        ORDER BY rc_date DESC, rc_no DESC
        LIMIT ?
    """, (lookback,))
    return [r[0] for r in cur.fetchall()]

def load_entries_by_race(con, race_id):
    cur = con.cursor()
    cur.execute("""
        SELECT horse_no, rank, win_odds
        FROM entries
        WHERE race_id = ?
    """, (race_id,))
    return cur.fetchall()

# -----------------------------
# 점수 계산 (Model A)
# -----------------------------
def score_horses(con, lookback):
    recent_races = load_recent_races(con, lookback)

    # 말별 누적 점수
    scores = defaultdict(float)
    counts = defaultdict(int)

    for rid in recent_races:
        rows = load_entries_by_race(con, rid)
        for horse_no, rank, win_odds in rows:
            odds = max(win_odds, ODDS_FLOOR)

            # 성적 점수: 1등 1.0, 2등 0.6, 3등 0.3, 그 외 0
            if rank == 1:
                perf = 1.0
            elif rank == 2:
                perf = 0.6
            elif rank == 3:
                perf = 0.3
            else:
                perf = 0.0

            # 배당 보정 (저배당 우대)
            odds_adj = 1.0 / odds

            scores[horse_no] += perf * odds_adj
            counts[horse_no] += 1

    # 평균화
    for h in scores:
        if counts[h] > 0:
            scores[h] /= counts[h]

    return scores

# -----------------------------
# 예측
# -----------------------------
def predict():
    con = sqlite3.connect(DB_PATH)

    scores = score_horses(con, LOOKBACK_RACES)
    con.close()

    if not scores:
        return {
            "decision": "PASS",
            "confidence": 0.0,
            "reason": "no_data"
        }

    horses = list(scores.keys())
    raw_scores = [scores[h] for h in horses]

    probs = softmax(raw_scores, TEMP)

    best_idx = max(range(len(probs)), key=lambda i: probs[i])
    best_horse = horses[best_idx]
    confidence = probs[best_idx]

    if confidence < PASS_THRESHOLD:
        return {
            "decision": "PASS",
            "confidence": round(confidence, 4),
            "reason": "low_confidence"
        }

    return {
        "decision": int(best_horse),
        "confidence": round(confidence, 4),
        "reason": "model_a"
    }

# -----------------------------
# 실행
# -----------------------------
if __name__ == "__main__":
    result = predict()
    print("PREDICTION RESULT")
    print(result)
