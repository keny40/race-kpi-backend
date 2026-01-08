from fastapi import APIRouter, Request, HTTPException
import os

from backend.services.kra_crawler import fetch_simple, upsert

router = APIRouter(prefix="/api/admin", tags=["admin"])

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
DB_PATH = "backend/races.db"


def _auth(request: Request):
    token = request.headers.get("x-admin-token")
    if token != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="unauthorized")


@router.get("/crawl")
def crawl(request: Request):
    _auth(request)

    rows = fetch_simple()
    inserted = upsert(DB_PATH, rows)

    return {
        "ok": True,
        "parsed": len(rows),
        "inserted": inserted,
    }
