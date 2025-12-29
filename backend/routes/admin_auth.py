from fastapi import APIRouter, Depends, HTTPException, Request
import os

router = APIRouter(prefix="/api/admin", tags=["admin-auth"])

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

def check_admin(request: Request):
    token = request.headers.get("x-admin-token")
    if not token or token != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="unauthorized")

@router.post("/login")
def admin_login(password: str):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="invalid password")
    return {"token": ADMIN_PASSWORD}
