from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
import sqlite3, os
from datetime import datetime

from backend.services.admin_state import set_state, get_state
from backend.services.admin_log import log_admin_action
from backend.services.slack_client import send_slack_message

router = APIRouter(prefix="/api/admin", tags=["admin"])

DB_PATH = os.getenv("DB_PATH", "races.db")

ADMIN_PASSWORD = "admin123"
ADMIN_COOKIE = "admin_token"


def require_admin(request: Request):
    token = request.cookies.get(ADMIN_COOKIE)
    if token != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Admin auth failed")


@router.post("/login")
def admin_login(payload: dict):
    if payload.get("password") != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid password")

    res = JSONResponse({"ok": True})
    res.set_cookie(
        key=ADMIN_COOKIE,
        value=ADMIN_PASSWORD,
        httponly=True,
        samesite="lax"
    )
    return res


@router.get("/state")
def admin_state(_: None = Depends(require_admin)):
    return get_state()


@router.post("/auto-red")
def set_auto_red(payload: dict, _: None = Depends(require_admin)):
    value = bool(payload["value"])
    set_state("auto_red", value)
    log_admin_action("AUTO_RED", str(value))
    send_slack_message(f"[ADMIN] AUTO_RED = {value}")
    return {"ok": True}


@router.post("/force-pass")
def set_force_pass(payload: dict, _: None = Depends(require_admin)):
    value = bool(payload["value"])
    set_state("force_pass", value)
    log_admin_action("FORCE_PASS", str(value))
    send_slack_message(f"[ADMIN] FORCE_PASS = {value}")
    return {"ok": True}


@router.post("/lock")
def set_lock(payload: dict, _: None = Depends(require_admin)):
    value = bool(payload["value"])
    set_state("locked", value)
    log_admin_action("LOCK", str(value))
    send_slack_message(f"[ADMIN] LOCK = {value}")
    return {"ok": True}


@router.get("/logs")
def get_admin_logs(_: None = Depends(require_admin)):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT action, value, created_at
        FROM admin_action_log
        ORDER BY id DESC
        LIMIT 50
    """).fetchall()
    conn.close()

    return [
        {"action": r[0], "value": r[1], "created_at": r[2]}
        for r in rows
    ]


@router.get("/red-score/history")
def red_score_history(_: None = Depends(require_admin)):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT created_at, status
        FROM system_status_log
        ORDER BY id DESC
        LIMIT 100
    """).fetchall()
    conn.close()

    score = 0
    data = []
    for ts, status in reversed(rows):
        score = score + 1 if status == "RED" else max(0, score - 1)
        data.append({"time": ts, "score": score})

    return data
