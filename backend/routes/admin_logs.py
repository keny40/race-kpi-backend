from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException
import os

from backend.services.ops_log import list_logs, clear_logs, init_ops_db

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
router = APIRouter(prefix="/api/admin", tags=["admin-logs"])


def _auth(req: Request):
    token = req.headers.get("x-admin-token", "")
    if not ADMIN_PASSWORD or token != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="unauthorized")


@router.get("/logs")
def get_logs(req: Request, limit: int = 200):
    _auth(req)
    init_ops_db()
    return {"items": list_logs(limit=limit)}


@router.post("/logs/clear")
def post_clear(req: Request):
    _auth(req)
    init_ops_db()
    return clear_logs()
