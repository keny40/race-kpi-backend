from fastapi import APIRouter
from backend.services.kpi_store import confidence_bins

router = APIRouter(prefix="/api/admin/stats", tags=["admin-stats"])

@router.get("/confidence_bins")
def get_bins():
    return {"ok": True, "bins": confidence_bins()}
