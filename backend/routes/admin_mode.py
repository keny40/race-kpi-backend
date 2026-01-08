from fastapi import APIRouter, Request, HTTPException
from backend.services.run_mode import get_mode, set_mode
import os

router = APIRouter(prefix="/api/admin", tags=["admin"])

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

def _auth(request: Request):
    token = request.headers.get("x-admin-token")
    if token != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="unauthorized")

@router.get("/mode")
def get_run_mode(request: Request):
    _auth(request)
    return {"mode": get_mode()}

@router.post("/mode/{mode}")
def set_run_mode(mode: str, request: Request):
    _auth(request)
    return {"mode": set_mode(mode)}
