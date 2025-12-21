from weights import select_weights
import random

def score_horse(h, w):
    s = 0.0
    if h.recent_rank is not None:
        s += max(0, 10 - h.recent_rank) * w["recent_rank"]
    if h.draw is not None:
        s += max(0, 6 - abs(h.draw - 6)) * w["draw"]
    if h.odds is not None:
        s += max(0, 10 - h.odds) * w["odds"]
    s += random.uniform(0, w["noise"])
    return s

def model_A(req):
    w = select_weights(req.distance, req.track)
    w["recent_rank"] *= 1.1  # 최근 성적 강조
    return run(req, w)

def model_B(req):
    w = select_weights(req.distance, req.track)
    w["odds"] *= 1.2        # 인기(배당) 강조
    return run(req, w)

def run(req, w):
    scored = [(h.horse_id, score_horse(h, w)) for h in req.horses]
    scored.sort(key=lambda x: x[1], reverse=True)
    total = sum(s for _, s in scored)
    confidence = round(scored[0][1] / total, 2) if total > 0 else 0.5
    return {
        "winner": scored[0][0],
        "confidence": confidence,
        "scores": scored
    }
