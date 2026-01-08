# backend/routes/admin_metrics.py
from fastapi import APIRouter, Request, HTTPException
import os
import time

router = APIRouter(prefix="/api/admin", tags=["admin"])

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")


def _auth(request: Request):
    token = request.headers.get("x-admin-token", "")
    if not ADMIN_PASSWORD or token != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="unauthorized")


@router.get("/status")
def admin_status(request: Request):
    _auth(request)
    return {
        "ok": True,
        "msg": "admin status minimal ok",
        "ts": int(time.time()),
    }
