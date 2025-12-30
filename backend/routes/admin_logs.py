import os
from fastapi import APIRouter, Request, HTTPException
from backend.services.operation_guard import fetch_logs

router = APIRouter(prefix="/api/admin", tags=["admin-logs"])

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

def _auth(req: Request):
    token = req.headers.get("x-admin-token")
    if token != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="unauthorized")

@router.get("/logs")
def get_admin_logs(req: Request, limit: int = 50):
    _auth(req)
    limit = max(1, min(int(limit), 500))
    return {
        "limit": limit,
        "items": fetch_logs(limit)
    }
