from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import json
import time

from backend.routes.admin import require_admin
from backend.services.red_score import get_red_score_state

router = APIRouter(prefix="/api/admin", tags=["admin-sse"])


@router.get("/red-score/stream")
def red_score_stream(_: None = Depends(require_admin)):
    def event_generator():
        while True:
            data = get_red_score_state()
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
