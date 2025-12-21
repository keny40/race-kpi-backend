from fastapi import APIRouter
from backend.services.kpi_service import fetch_kpi_rows, compute_kpi_rows

router = APIRouter(prefix="/kpi", tags=["kpi"])


@router.get("/matrix")
def kpi_matrix():
    rows = fetch_kpi_rows()
    data = compute_kpi_rows(rows)

    matrix = []
    for model, r in data.items():
        for bin_key, v in r["confidence_bins"].items():
            matrix.append({
                "model": model,
                "confidence_bin": bin_key,
                "hit": v["hit"],
                "miss": v["miss"]
            })

    return matrix
