import sqlite3
from collections import defaultdict
from math import exp, sqrt

DB_PATH = "races.db"

# =============================
# 공통 유틸
# =============================
def softmax(scores, temp=1.0):
    exps = [exp(s / temp) for s in scores]
    s = sum(exps)
    return [e / s for e in exps] if s > 0 else [0 for _ in scores]


def load_recent_races(con, limit):
    cur = con.cursor()
    cur.execute("""
        SELECT DISTINCT race_id
        FROM races
        ORDER BY rc_date DESC, rc_no DESC
        LIMIT ?
    """, (limit,))
    return [r[0] for r in cur.fetchall()]


def load_entries(con, race_id):
    cur = con.cursor()
    cur.execute("""
        SELECT horse_no, rank, win_odds
        FROM entries
        WHERE race_id = ?
    """, (race_id,))
    return cur.fetchall()


# =============================
# Model A (안정형)
# =============================
def model_a_predict(
    lookback=3,
    pass_threshold=0.55,
    temp=1.5
):
    con = sqlite3.connect(DB_PATH)

    races = load_recent_races(con, lookback)
    scores = defaultdict(float)
    counts = defaultdict(int)

    for rid in races:
        for horse_no, rank, odds in load_entries(con, rid):
            if rank == 1:
                perf = 1.0
            elif rank == 2:
                perf = 0.6
            elif rank == 3:
                perf = 0.3
            else:
                perf = 0.0

            odds_adj = 1.0 / max(odds, 1.01)
            scores[horse_no] += perf * odds_adj
            counts[horse_no] += 1

    con.close()

    for h in scores:
        scores[h] /= max(counts[h], 1)

    if not scores:
        return {"decision": "PASS", "confidence": 0.0, "model": "A"}

    horses = list(scores.keys())
    probs = softmax([scores[h] for h in horses], temp)

    idx = max(range(len(probs)), key=lambda i: probs[i])
    if probs[idx] < pass_threshold:
        return {"decision": "PASS", "confidence": round(probs[idx], 4), "model": "A"}

    return {
        "decision": int(horses[idx]),
        "confidence": round(probs[idx], 4),
        "model": "A"
    }


# =============================
# Model B (변화·공격형)
# =============================
def model_b_predict(
    lookback=5,
    pass_threshold=0.50,
    temp=1.2
):
    con = sqlite3.connect(DB_PATH)

    races = load_recent_races(con, lookback)
    scores = defaultdict(list)

    for rid in races:
        for horse_no, rank, odds in load_entries(con, rid):
            # Top-3 진입 강조
            if rank <= 3:
                base = 1.0 / rank
            else:
                base = 0.0

            # 중배당 가중 (너무 낮거나 높으면 감점)
            odds_score = 1.0 - abs(odds - 6.0) / 6.0
            odds_score = max(odds_score, 0)

            scores[horse_no].append(base * odds_score)

    con.close()

    final_scores = {}
    for h, vals in scores.items():
        if len(vals) < 2:
            continue
        mean = sum(vals) / len(vals)
        var = sqrt(sum((v - mean) ** 2 for v in vals) / len(vals))
        final_scores[h] = mean + var  # 변동성 보너스

    if not final_scores:
        return {"decision": "PASS", "confidence": 0.0, "model": "B"}

    horses = list(final_scores.keys())
    probs = softmax([final_scores[h] for h in horses], temp)

    idx = max(range(len(probs)), key=lambda i: probs[i])
    if probs[idx] < pass_threshold:
        return {"decision": "PASS", "confidence": round(probs[idx], 4), "model": "B"}

    return {
        "decision": int(horses[idx]),
        "confidence": round(probs[idx], 4),
        "model": "B"
    }
