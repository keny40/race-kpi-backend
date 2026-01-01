from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
import sqlite3
from pathlib import Path

from backend.services.season import SeasonManager
from backend.services.risk_guard import evaluate_and_maybe_pause

DB_PATH = Path("races.db")
router = APIRouter(prefix="/api", tags=["predict"])

def _conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

class PredictRequest(BaseModel):
    race_id: str
    horses: list[dict] | None = None
    meta: dict | None = None

@router.post("/predict")
def predict(req: PredictRequest):
    ok, reason = SeasonManager.require_not_paused()
    if not ok:
        raise HTTPException(status_code=423, detail=f"paused: {reason}")

    race_id = req.race_id.strip()

    features = {
        "volatility": float((req.meta or {}).get("volatility", 0.10)),
        "disagreement": float((req.meta or {}).get("disagreement", 0.10)),
        "data_quality": float((req.meta or {}).get("data_quality", 0.90)),
    }

    guard = evaluate_and_maybe_pause(
        race_id=race_id,
        features=features,
        meta={"source": "predict", "client_meta": req.meta or {}}
    )

    decision = "PASS"
    confidence = 0.50

    if guard["is_red"]:
        decision = "PASS"
        confidence = 0.10
    else:
        decision = "PICK"
        confidence = 0.70

    con = _conn()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            race_id TEXT PRIMARY KEY,
            decision TEXT NOT NULL,
            confidence REAL NOT NULL,
            created_at TEXT NOT NULL,
            red_score REAL NOT NULL,
            red_threshold REAL NOT NULL,
            red_reason TEXT NOT NULL
        )
    """)
    cur.execute("""
        INSERT OR REPLACE INTO predictions
        (race_id, decision, confidence, created_at, red_score, red_threshold, red_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        race_id,
        decision,
        float(confidence),
        datetime.utcnow().isoformat(),
        float(guard["score"]),
        float(guard["threshold"]),
        str(guard["reason"])
    ))
    con.commit()
    con.close()

    return {
        "race_id": race_id,
        "decision": decision,
        "confidence": confidence,
        "risk": guard,
        "season": SeasonManager.get_status()
    }
