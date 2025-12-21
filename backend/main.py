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

app = FastAPI(title="Race Result Ingest API")

@app.on_event("startup")
def startup():
    bootstrap_db()
    start_scheduler()

app.include_router(strategy_state_router, prefix="/api")
app.include_router(kpi_matrix_router, prefix="/api")      # (전체/기존 유지)
app.include_router(kpi_summary_router, prefix="/api")     # 월/분기 KPI
app.include_router(kpi_report_router, prefix="/api")      # 월/분기 PDF + 발송
app.include_router(kpi_testdata_router, prefix="/api")    # 테스트 주입
app.include_router(kpi_trend_router, prefix="/api")
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")
