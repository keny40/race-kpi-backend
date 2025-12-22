from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.scheduler import start_scheduler
from backend.services.db_bootstrap import bootstrap_db

from backend.routes.kpi_matrix import router as kpi_matrix_router
from backend.routes.strategy_state import router as strategy_state_router
from backend.routes.kpi_report import router as kpi_report_router
from backend.routes.kpi_testdata import router as kpi_testdata_router
from backend.routes.kpi_summary import router as kpi_summary_router
from backend.routes.kpi_trend import router as kpi_trend_router

# 🔴 추가
from backend.routes.predict import router as predict_router
from backend.routes.result import router as result_router

import os

app = FastAPI(title="Race Result Ingest API")

@app.on_event("startup")
def startup():
    bootstrap_db()
    start_scheduler()

# ===== 기존 KPI 라우터 =====
app.include_router(strategy_state_router, prefix="/api")
app.include_router(kpi_matrix_router, prefix="/api")
app.include_router(kpi_summary_router, prefix="/api")
app.include_router(kpi_report_router, prefix="/api")
app.include_router(kpi_testdata_router, prefix="/api")
app.include_router(kpi_trend_router, prefix="/api")

# ===== 🔴 예측 / 결과 =====
app.include_router(predict_router, prefix="/api")
app.include_router(result_router, prefix="/api")

# ===== Static =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

if os.path.isdir(STATIC_DIR):
    app.mount(
        "/static",
        StaticFiles(directory=STATIC_DIR, html=True),
        name="static"
    )
