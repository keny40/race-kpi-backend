# backend/services/mock_race_data.py

import random
import uuid
from datetime import datetime


def generate_mock_race():
    """
    MOCK 경마 데이터 1건 생성
    실데이터 구조를 최대한 유사하게 구성
    """

    race_id = f"MOCK_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    horse_count = random.randint(7, 14)
    horses = []

    total_prob = 0.0
    for i in range(horse_count):
        prob = random.uniform(0.03, 0.25)
        total_prob += prob
        horses.append({
            "horse_no": i + 1,
            "win_prob": prob
        })

    # 확률 정규화
    for h in horses:
        h["win_prob"] = round(h["win_prob"] / total_prob, 4)

    # 실제 결과 (확률 기반)
    r = random.random()
    cumulative = 0.0
    winner = None

    for h in horses:
        cumulative += h["win_prob"]
        if r <= cumulative:
            winner = h["horse_no"]
            break

    if winner is None:
        winner = horses[-1]["horse_no"]

    return {
        "race_id": race_id,
        "generated_at": datetime.utcnow().isoformat(),
        "track": random.choice(["서울", "부산", "제주"]),
        "race_no": random.randint(1, 12),
        "horses": horses,
        "winner": winner
    }
