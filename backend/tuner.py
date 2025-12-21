# backend/tuner.py
from __future__ import annotations
from typing import Dict, Any


class Tuner:
    def __init__(self):
        self.default: Dict[str, Any] = {
            "model_w": 0.5,
            "db_w": 0.5,
            "thresh": 0.66,
        }
        self.by_season: Dict[str, Dict[str, Any]] = {}

    def get_params(self, season_key: str | None) -> Dict[str, Any]:
        if not season_key:
            return dict(self.default)
        return dict(self.by_season.get(season_key, self.default))

    def update(self, season_key: str, params: Dict[str, Any]) -> None:
        merged = dict(self.default)
        merged.update(params or {})
        self.by_season[season_key] = merged
