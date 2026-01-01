# backend/routes/sse.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import time
import json
from backend.services.log_store import query_logs

router = APIRouter(prefix="/sse", tags=["sse"])

@router.get("/ops")
def sse_ops():
    def gen():
        last = 0
        while True:
            rows = query_logs(limit=10)
            payload = json.dumps(rows, ensure_ascii=False)
            yield f"data: {payload}\n\n"
            time.sleep(2)
    return StreamingResponse(gen(), media_type="text/event-stream")
