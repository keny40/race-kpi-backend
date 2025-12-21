from pydantic import BaseModel
from typing import Optional, Dict, Any


class PredictRequest(BaseModel):
    race_id: str
    horse_no: int
    season_key: Optional[str] = None
    additional: Dict[str, Any] = {}


class WinnerPredictRequest(BaseModel):
    race_id: str
    season_key: Optional[str] = None
    additional: Dict[str, Any] = {}


class DecisionDTO(BaseModel):
    label: str
    confidence: float
    meta: Dict[str, Any]
