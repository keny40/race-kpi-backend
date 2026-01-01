def _safe_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default

def calculate_confidence(race: dict) -> float:
    """
    3개 feature 기반 confidence (0~1)
    - jockey_win_rate
    - recent_rank_avg
    - distance_fit (거리 가중치, MOCK에서 의미)
    REAL(HTML raw)에서도 안전하게 0.4 근처로 수렴
    """
    if not race:
        return 0.4

    horses = race.get("horses") or []
    distance = race.get("distance")

    # REAL-HTML raw 형태면 horses가 dict(raw) 리스트일 수 있어 feature가 없다 → 안전한 기본값
    if not horses or not isinstance(horses, list):
        return 0.4

    scores = []
    for h in horses:
        # MOCK에서는 숫자 feature 존재
        jw = _safe_float(h.get("jockey_win_rate", 0.12), 0.12)
        rr = _safe_float(h.get("recent_rank_avg", 5.0), 5.0)

        # 거리 적합도(임시): 1200~1600 구간이면 약간 가산, 아니면 중립
        if isinstance(distance, (int, float)):
            distance_fit = 1.0 if 1200 <= distance <= 1600 else 0.85
        else:
            distance_fit = 0.9

        # recent_rank_avg 낮을수록 좋게 (1~10 가정)
        rank_score = max(0.0, min(1.0, 1 - (rr / 10.0)))

        score = (
            rank_score * 0.55 +
            jw * 0.30 +
            distance_fit * 0.15
        )
        scores.append(score)

    if not scores:
        return 0.4

    avg_score = sum(scores) / len(scores)

    # 0~1 클램프 + 소수 2자리
    if avg_score < 0:
        avg_score = 0.0
    if avg_score > 1:
        avg_score = 1.0

    return round(avg_score, 2)
