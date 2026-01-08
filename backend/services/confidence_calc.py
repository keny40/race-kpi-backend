import statistics

def calc_confidence(scores: list[float], recent_avg: float | None = None) -> float:
    if len(scores) < 2:
        return 0.0

    scores = sorted(scores, reverse=True)
    gap = scores[0] - scores[1]
    variance = statistics.pvariance(scores)

    base = gap * (1 / (1 + variance))

    if recent_avg is not None:
        base *= (0.8 + 0.4 * recent_avg)

    return round(min(max(base, 0), 1), 3)
