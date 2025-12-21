from fastapi import APIRouter
from backend.ai_ensemble import model_a_predict, model_b_predict
from backend.services.kpi_service import record_prediction

router = APIRouter(tags=["predict"])

@router.get("/predict")
def predict(model: str = "A", race_id: str = "TEST_RACE"):
    model = model.upper()

    if model == "A":
        result = model_a_predict()
    elif model == "B":
        result = model_b_predict()
    else:
        return {"decision": "PASS", "confidence": 0.0, "reason": "invalid_model"}

    record_prediction(
        race_id=race_id,
        model=model,
        decision=result["decision"],
        confidence=result["confidence"]
    )

    return result
