from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.routes.predict import router as predict_router
from backend.routes.result import router as result_router   # 🔴 추가

app = FastAPI(title="Race Result Ingest API")

# 기존 startup / scheduler 그대로 유지

app.include_router(predict_router, prefix="/api")   # 이미 있다면 유지
app.include_router(result_router)                    # 🔴 이 줄이 핵심
