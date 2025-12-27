import os
from fastapi import HTTPException, Request

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


def check_admin(request: Request):
    token = request.headers.get("X-Admin-Token")
    if token != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Admin auth failed")
