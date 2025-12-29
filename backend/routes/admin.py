from fastapi import APIRouter, Request, HTTPException
import sqlite3

from backend.services.system_state import get_state, set_state
from backend.services.strategy_state import force_pass, force_pass_off
from backend.services.admin_log import log_admin_action

DB_PATH = "races.db"

router = APIRouter(prefix="/api/admin", tags=["admin"])

def _auth(request: Request):
    token = request.headers.get("x-admin-token")
    if not token:
        raise HTTPException(status_code=401, detail="unauthorized")

def _conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

# FORCE PASS ON
@router.post("/force-pass/on")
def force_pass_on(request: Request):
    _auth(request)
    force_pass(reason="MANUAL")
    return {"status": "ok"}

# FORCE PASS OFF
@router.post("/force-pass/off")
def force_pass_off_api(request: Request):
    _auth(request)
    force_pass_off()
    return {"status": "ok"}

# 최근 관리자 로그
@router.get("/logs/recent")
def recent_logs(request: Request, limit: int = 5):
    _auth(request)
    con = _conn()
    cur = con.cursor()
    rows = cur.execute(
        """
        SELECT action, reason, created_at
        FROM admin_action_log
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    con.close()

    return [
        {"action": r["action"], "reason": r["reason"], "at": r["created_at"]}
        for r in rows
    ]

# 임계치 설정
@router.post("/thresholds")
async def update_thresholds(request: Request):
    _auth(request)
    data = await request.json()

    if "red_notify_n" in data:
        set_state("red_notify_n", str(int(data["red_notify_n"])))
    if "green_release_n" in data:
        set_state("green_release_n", str(int(data["green_release_n"])))

    log_admin_action("THRESHOLD_UPDATE", str(data))
    return {"status": "ok"}
