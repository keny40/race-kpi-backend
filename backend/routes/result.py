from fastapi import APIRouter

router = APIRouter(
    prefix="/api/result",
    tags=["result"]
)

@router.post("/actual")
def post_actual(payload: dict):
    return {
        "status": "ok",
        "payload": payload
    }
