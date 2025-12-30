from fastapi import APIRouter
from fastapi.responses import StreamingResponse, FileResponse
from backend.services.strategy_state import (
    enable_force_pass,
    disable_force_pass,
    is_force_pass_enabled,
)
from backend.services.admin_log import log_admin_action, get_logs
from backend.services.slack_notifier import send_admin_action
from backend.services.pdf_generator import generate_admin_log_pdf

router = APIRouter(prefix="/api/admin", tags=["admin-control"])


@router.post("/force-pass/on")
def force_pass_on():
    enable_force_pass(reason="MANUAL")
    log_admin_action("FORCE_PASS_ON", "manual")
    send_admin_action("FORCE_PASS_ON", "manual")
    return {"status": "ok"}


@router.post("/force-pass/off")
def force_pass_off():
    disable_force_pass()
    log_admin_action("FORCE_PASS_OFF", "manual")
    send_admin_action("FORCE_PASS_OFF", "manual")
    return {"status": "ok"}


@router.get("/status")
def admin_status():
    return {"force_pass": is_force_pass_enabled()}


@router.get("/logs")
def admin_logs():
    return get_logs()


@router.get("/logs.csv")
def download_logs_csv():
    logs = get_logs()

    def gen():
        yield "created_at,action,detail\n"
        for r in logs:
            yield f"{r['created_at']},{r['action']},{r['detail']}\n"

    return StreamingResponse(
        gen(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=admin_logs.csv"},
    )


@router.get("/logs.pdf")
def download_logs_pdf():
    path = generate_admin_log_pdf()
    return FileResponse(
        path,
        media_type="application/pdf",
        filename="admin_logs.pdf",
    )
