# backend/ops_routes.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

from .ops_reporting import build_and_save_report_pdf

router = APIRouter(prefix="/api/ops", tags=["ops"])


@router.get("/report/pdf")
def report_pdf(period: str = "monthly"):
    """
    period: monthly | quarterly
    생성된 PDF 파일 경로를 반환하며, 바로 다운로드도 가능하게 FileResponse로 응답
    """
    try:
        path = build_and_save_report_pdf(period=period)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not os.path.exists(path):
        raise HTTPException(status_code=500, detail="pdf file not created")

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=os.path.basename(path),
    )
