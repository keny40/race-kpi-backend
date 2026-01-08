# backend/services/mock_predictor.py
import random

def mock_predict(race):
    """
    MOCK 예측기
    - 말 번호 1~14 중 랜덤
    - confidence 0.55~0.85
    """
    horse_no = random.randint(1, 14)
    confidence = round(random.uniform(0.55, 0.85), 2)

    return {
        "race_id": race["race_id"],
        "predicted_horse_no": horse_no,
        "confidence": confidence,
        "passed": 0,
        "strategy": "MOCK"
    }
