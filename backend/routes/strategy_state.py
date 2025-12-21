from fastapi import APIRouter
from backend.services.strategy_policy import get_strategy_state

router = APIRouter()

@router.get("/strategy/state")
def strategy_state():
    return get_strategy_state()
