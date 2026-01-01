# backend/routes/stream.py
import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.services.risk_guard import get_status_snapshot

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "races.db"

router = APIRouter(prefix="/api/stream", tags=["stream"])


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/status")
async def sse_status():
    """
    UI 상단 상태/배지 실시간 유지
    - 1초 주기로 스냅샷 푸시
    - EventSource 자동 reconnect 대응
    """
    async def gen():
        last_payload = None
        while True:
            snap = get_status_snapshot()
            payload = {
                "ts": datetime.utcnow().isoformat(),
                **snap,
            }
            data = json.dumps(payload, ensure_ascii=False)

            # 중복 전송 줄이기(깜빡임 방지)
            if data != last_payload:
                yield f"event: status\ndata: {data}\n\n"
                last_payload = data

            # keepalive
            yield f": ping {int(datetime.utcnow().timestamp())}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.get("/history")
async def sse_history():
    """
    최근 risk_history 변화가 있을 때만 푸시 (차트 업데이트용)
    """
    async def gen():
        last_id = 0
        while True:
            try:
                conn = _conn()
                cur = conn.cursor()
                row = cur.execute("SELECT id, created_at, score, threshold, streak, is_red, paused, reason FROM risk_history ORDER BY id DESC LIMIT 1").fetchone()
                conn.close()

                if row and int(row["id"]) != last_id:
                    last_id = int(row["id"])
                    payload = {
                        "id": last_id,
                        "created_at": row["created_at"],
                        "score": float(row["score"]),
                        "threshold": float(row["threshold"]),
                        "streak": int(row["streak"]),
                        "is_red": bool(row["is_red"]),
                        "paused": bool(row["paused"]),
                        "reason": row["reason"],
                    }
                    yield f"event: history\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

            except Exception:
                # 끊기지 않게 keepalive만
                pass

            yield f": ping {int(datetime.utcnow().timestamp())}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(gen(), media_type="text/event-stream")
