from fastapi import APIRouter, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.services.admin_auth import check_admin
from backend.services.system_control import get_state, set_state
from backend.services.red_score import calc_red_score, explain_score, get_recent_statuses
from backend.services.pdf_red_report import build_red_report_pdf

router = APIRouter(prefix="/api/admin", tags=["admin"])


class ToggleRequest(BaseModel):
    value: bool


@router.get("/state")
def state(req: Request):
    check_admin(req)
    return get_state()


@router.post("/auto-red")
def auto_red(req: Request, body: ToggleRequest):
    check_admin(req)
    set_state("auto_red", body.value)
    return {"auto_red": body.value}


@router.post("/force-pass")
def force_pass(req: Request, body: ToggleRequest):
    check_admin(req)
    set_state("force_pass", body.value)
    return {"force_pass": body.value}


@router.post("/red-lock")
def red_lock(req: Request, body: ToggleRequest):
    check_admin(req)
    set_state("red_lock", body.value)
    return {"red_lock": body.value}


@router.get("/red-score")
def red_score(req: Request):
    check_admin(req)
    return {
        "score": calc_red_score(),
        "explain": explain_score(),
        "recent": get_recent_statuses(limit=60)
    }


@router.get("/red-report.pdf")
def red_report_pdf(req: Request):
    check_admin(req)
    path = build_red_report_pdf()
    return FileResponse(path, filename="red_report.pdf")
