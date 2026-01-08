# backend/routes/admin_upload.py
from fastapi import APIRouter, UploadFile, File
from backend.services.rpt_data_source import load_rpt
from backend.services.predict_runner import run_predict_for_all  # 추후 연결

router = APIRouter(prefix="/api/admin", tags=["admin-upload"])

@router.post("/upload_rpt")
async def upload_rpt(file: UploadFile = File(...)):
    content = await file.read()

    # TODO: 실제 RPT 파서 결과로 교체
    races = [
        {
            "race_id": "20260103_01",
            "race_no": 1,
            "distance": 1200,
            "start_time": "10:35",
            "grade": "국6"
        }
    ]
    race_details = {
        "20260103_01": {
            "horses": [],
            "predict": {}
        }
    }

    load_rpt(races, race_details)

    # 🔥 여기서 1회 예측 자동 실행
    # run_predict_for_all()

    return {
        "ok": True,
        "races": len(races)
    }
