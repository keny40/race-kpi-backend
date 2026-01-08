from fastapi import APIRouter

router = APIRouter(tags=["admin-pre-race"])

@router.get("/rules")
def get_rules():
    return {
        "confidence_threshold": 0.65,
        "auto_pause": True
    }

@router.post("/rules")
def save_rules(payload: dict):
    return {"ok": True}
