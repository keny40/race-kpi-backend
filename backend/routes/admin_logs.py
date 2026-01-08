# backend/routes/admin_logs.py
from fastapi import APIRouter, Request, HTTPException
import os

from backend.services.log_store import query_logs

router = APIRouter(prefix="/api/admin", tags=["admin-logs"])

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")


def _auth(request: Request):
    token = request.headers.get("x-admin-token", "")
    if not ADMIN_PASSWORD or token != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="unauthorized")


@router.get("/logs")
def get_logs(request: Request, limit: int = 50):
    _auth(request)
    return query_logs(limit=limit)
