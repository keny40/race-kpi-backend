# routes/report.py
from fastapi import APIRouter

from report_generator import generate_performance_pdf
from executive_report import generate_executive_pdf

router = APIRouter(prefix="/api/report", tags=["report"])


@router.post("/generate")
def generate_report(period: str = "monthly"):
    """
    period = monthly | quarterly
    """
    path = generate_performance_pdf(period=period)
    return {
        "status": "OK",
        "period": period,
        "file": path,
    }


@router.post("/executive")
def generate_executive():
    """
    경영진 1페이지 요약 PDF
    """
    path = generate_executive_pdf()
    return {
        "status": "OK",
        "file": path,
    }
