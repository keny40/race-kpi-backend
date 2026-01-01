from typing import List, Dict
from backend.services.kra_html_fetcher import fetch_race_list

def load_replay_data(
    mode: str = "MOCK",
    date: str | None = None
) -> List[Dict]:
    if mode == "REAL":
        if not date:
            raise ValueError("REAL mode requires date (YYYYMMDD)")
        try:
            return fetch_race_list(date)
        except Exception as e:
            # REAL 실패 시 MOCK으로 안전 전환
            print(f"[REPLAY] REAL fetch failed, fallback to MOCK: {e}")

    return [
        {
            "race_id": "MOCK-R1",
            "horses": [
                {"no": "1", "name": "A"},
                {"no": "2", "name": "B"},
                {"no": "3", "name": "C"},
            ]
        }
    ]
