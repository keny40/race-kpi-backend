from fastapi import APIRouter
from backend.services.rpt_data_source import load_rpt

router = APIRouter(prefix="/api/admin", tags=["admin-rpt"])

@router.get("/rpt_status")
def rpt_status():
    data = load_rpt()
    return {
        "ok": True,
        "source": data["source"],
        "counts": data["counts"]
    }
