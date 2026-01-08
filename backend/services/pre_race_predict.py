import random
from datetime import datetime


def run_pre_race_predict():
    """
    pre-race 예측 MOCK 함수
    실제 모델 연결 전 임시 구현
    """

    race_id = f"MOCK_RACE_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    scores = []
    for horse_no in range(1, 11):
        scores.append({
            "horse_no": horse_no,
            "score": round(random.uniform(0.3, 0.95), 4)
        })

    confidence = max(s["score"] for s in scores)

    summary = {
        "top_horses": sorted(scores, key=lambda x: x["score"], reverse=True)[:3],
        "all_scores": scores,
        "generated_by": "MOCK"
    }

    return {
        "race_id": race_id,
        "scores": scores,
        "confidence": confidence,
        "summary": summary
    }
