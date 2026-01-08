# backend/services/judge.py

def judge(predicted: int | None, winner: int) -> str:
    if predicted is None:
        return "PASS"
    return "HIT" if predicted == winner else "MISS"
