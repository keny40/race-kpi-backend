from datetime import datetime

class SeasonManager:
    def __init__(self):
        self._seasons = [
            {"id": "2023-H1", "start": "2023-01-01", "end": "2023-06-30"},
            {"id": "2023-H2", "start": "2023-07-01", "end": "2023-12-31"},
            {"id": "2024-H1", "start": "2024-01-01", "end": "2024-06-30"},
            {"id": "2024-H2", "start": "2024-07-01", "end": "2024-12-31"},
        ]

    def get_seasons(self):
        return self._seasons

    def get_current_season(self):
        now = datetime.utcnow().date()
        for s in self._seasons:
            start = datetime.fromisoformat(s["start"]).date()
            end = datetime.fromisoformat(s["end"]).date()
            if start <= now <= end:
                return s
        return None
