# backend/services/predict_runner.py (신규)
from datetime import datetime
from backend.services.rpt_data_source import list_races, set_predict
from backend.services.predict_config import PREDICT_CONFIG

def decide(confidence: float) -> str:
    return "GO" if confidence >= PREDICT_CONFIG["confidence_threshold"] else "PASS"



def run_predict_for_all():
    for r in list_races():
        rid = r["race_id"]
        # TODO: 실제 모델 연결
        predict = {
            "race_id": rid,
            "decision": "GO",
            "confidence": 0.72,
            "top_horses": [3,7,1],
            "engine_votes": {"RECENCY":0.68,"MARKOV":0.75,"KNN":0.70},
            "timestamp": datetime.utcnow().isoformat()
        }
        set_predict(rid, predict)
