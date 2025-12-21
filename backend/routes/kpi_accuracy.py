from fastapi import APIRouter
from backend.services.kpi_service import fetch_accuracy_kpi

router = APIRouter(tags=["kpi-accuracy"])

@router.get("/kpi/accuracy")
def get_accuracy():
    return fetch_accuracy_kpi()
