from backend.services.pre_race_history_store import save_pre_race_history

# 예측 결과 가정
scores = [
    {"horse_no": 3, "score": 0.82},
    {"horse_no": 7, "score": 0.74},
    {"horse_no": 1, "score": 0.68},
]

confidence = 0.78
decision = "BET" if confidence >= 0.65 else "PASS"

summary = {
    "top_horses": scores[:3],
    "total_horses": len(scores),
    "engine": "pre-race-v1",
}

save_pre_race_history(
    race_id=race_id,
    summary=summary,
    confidence=confidence,
    decision=decision,
)
