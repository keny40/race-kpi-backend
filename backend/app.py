from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.predict import router as predict_router
from backend.routes.result_actual import router as result_router

from backend.routes.kpi_summary import router as kpi_summary_router
from backend.routes.kpi_trend import router as kpi_trend_router
from backend.routes.kpi_match import router as kpi_match_router
from backend.routes.kpi_notify import router as kpi_notify_router
from backend.routes.kpi_threshold import router as kpi_threshold_router
from backend.routes.kpi_strategy import router as kpi_strategy_router
from backend.routes.kpi_report import router as kpi_report_router

app = FastAPI(title="Race KPI Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 기본
app.include_router(predict_router)
app.include_router(result_router)

# KPI
app.include_router(kpi_summary_router)
app.include_router(kpi_trend_router)
app.include_router(kpi_match_router)
app.include_router(kpi_notify_router)
app.include_router(kpi_threshold_router)
app.include_router(kpi_strategy_router)
app.include_router(kpi_report_router)


@app.get("/")
def root():
    return {"status": "ok"}
