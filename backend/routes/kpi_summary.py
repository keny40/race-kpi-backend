from fastapi import APIRouter
from backend.services.kpi_service import fetch_kpi_rows, compute_kpi_rows

router = APIRouter(prefix="/kpi", tags=["kpi"])


@router.get("/summary")
def kpi_summary():
    rows = fetch_kpi_rows()
    return compute_kpi_rows(rows)
