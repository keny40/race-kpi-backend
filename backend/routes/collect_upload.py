from fastapi import APIRouter, UploadFile, File, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from backend.services.collect_service import parse_and_insert_upload

router = APIRouter(prefix="/api/collect", tags=["collect"])


class CollectUploadResponse(BaseModel):
    ok: bool = Field(..., example=True)
    inserted: int = Field(..., example=12)
    skipped: int = Field(..., example=3)
    errors: List[str] = Field(
        default_factory=list,
        example=[]
    )
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        example={
            "filename": "dummy_races.csv",
            "trigger_prerace": True
        }
    )

    class Config:
        schema_extra = {
            "example": {
                "ok": True,
                "inserted": 12,
                "skipped": 3,
                "errors": [],
                "meta": {
                    "filename": "dummy_races.csv",
                    "trigger_prerace": True
                }
            }
        }


@router.post(
    "/upload",
    response_model=CollectUploadResponse,
    summary="CSV/XLSX 업로드 및 pre-race 트리거",
)
async def upload_file(
    file: UploadFile = File(...),
    trigger_prerace: int = Query(0, description="1이면 pre-race 요약 생성"),
):
    return await parse_and_insert_upload(
        file=file,
        trigger_prerace=bool(trigger_prerace),
    )
