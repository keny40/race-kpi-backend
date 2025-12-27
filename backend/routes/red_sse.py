import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.services.red_score import calc_red_score

router = APIRouter(tags=["sse"])


@router.get("/api/admin/red-stream")
async def red_stream():
    async def event_gen():
        last = None
        while True:
            score = calc_red_score()
            if score != last:
                yield f"data: {score}\n\n"
                last = score
            await asyncio.sleep(3)

    return StreamingResponse(event_gen(), media_type="text/event-stream")
