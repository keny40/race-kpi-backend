# backend/services/rpt_data_source.py
"""
RPT 기반 경주 데이터 단일 소스
- RPT 업로드 시 load_rpt()로 메모리 적재
- 모든 API는 여기 데이터만 참조
"""

from typing import List, Dict, Any

# ===== In-memory store =====
_RACES: List[Dict[str, Any]] = []
_RACE_DETAIL: Dict[str, Dict[str, Any]] = {}

# ===== Load =====
def load_rpt(races: List[Dict[str, Any]], race_details: Dict[str, Dict[str, Any]]):
    global _RACES, _RACE_DETAIL
    _RACES = races or []
    _RACE_DETAIL = race_details or {}

# ===== List =====
def list_races() -> List[Dict[str, Any]]:
    return _RACES

# ===== Get single race =====
def get_race(race_id: str) -> Dict[str, Any] | None:
    for r in _RACES:
        if r.get("race_id") == race_id:
            return r
    return None

# ===== Detail =====
def get_race_detail(race_id: str) -> Dict[str, Any] | None:
    return _RACE_DETAIL.get(race_id)

# rpt_data_source.py 하단에 추가
def set_predict(race_id: str, predict: dict):
    if race_id not in _RACE_DETAIL:
        _RACE_DETAIL[race_id] = {}
    _RACE_DETAIL[race_id]["predict"] = predict
