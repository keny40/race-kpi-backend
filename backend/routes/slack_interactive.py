# backend/routes/slack_interactive.py
from fastapi import APIRouter, Request
from backend.services.strategy_state import set_strategy_enabled
import json

router = APIRouter(prefix="/api/slack", tags=["slack"])

@router.post("/action")
async def slack_action(req: Request):
    payload = json.loads((await req.form())["payload"])
    action = payload["actions"][0]
    strategy = action["value"]

    set_strategy_enabled(strategy, True)
    return {"text": f"✅ Strategy `{strategy}` re-enabled"}
