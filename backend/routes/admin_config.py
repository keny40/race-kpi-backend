# backend/routes/admin_config.py
from fastapi import APIRouter
from pydantic import BaseModel
from backend.services.predict_config import PREDICT_CONFIG

router = APIRouter(prefix="/api/admin/config", tags=["admin-config"])

class ThresholdBody(BaseModel):
    value: float

class PrestartBody(BaseModel):
    enabled: bool

class MinutesBody(BaseModel):
    minutes: int

@router.get("")
def get_config():
    return {"ok": True, **PREDICT_CONFIG}

@router.post("/threshold")
def set_threshold(body: ThresholdBody):
    v = float(body.value)
    if v < 0.0: v = 0.0
    if v > 1.0: v = 1.0
    PREDICT_CONFIG["confidence_threshold"] = v
    return {"ok": True, "confidence_threshold": v}

@router.post("/prestart")
def set_prestart(body: PrestartBody):
    PREDICT_CONFIG["enable_prestart_repredict"] = bool(body.enabled)
    return {"ok": True, "enable_prestart_repredict": PREDICT_CONFIG["enable_prestart_repredict"]}

@router.post("/minutes")
def set_minutes(body: MinutesBody):
    m = int(body.minutes)
    if m < 1: m = 1
    if m > 60: m = 60
    PREDICT_CONFIG["minutes_before_start"] = m
    return {"ok": True, "minutes_before_start": m}
