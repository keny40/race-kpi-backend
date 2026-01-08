import random

def run_strategy(features):
    """
    REAL 경주 전 데이터 기반 baseline 전략
    - odds(배당) 기반 간단 점수화
    """

    raw = features["raw"]          # 말별 정보 리스트
    field_size = features["field_size"]

    scored = []
    for h in raw:
        # 낮은 배당일수록 유리 (간단 역수)
        win_odds = h.get("winOdds", 50.0)
        score = 1.0 / max(win_odds, 1.01)

        scored.append({
            "horse_no": int(h["horseNo"]),
            "score": score,
            "win_odds": win_odds
        })

    scored.sort(key=lambda x: x["score"], reverse=True)

    top = scored[0]
    confidence = min(0.95, top["score"] * field_size)

    # PASS 규칙 (예시)
    is_pass = confidence < 0.55

    return {
        "horse_no": top["horse_no"],
        "confidence": round(confidence, 3),
        "pass": is_pass,
        "strategy": "ODDS_BASELINE",
        "threshold": 0.55,
        "ranking_json": str(scored[:5])
    }
