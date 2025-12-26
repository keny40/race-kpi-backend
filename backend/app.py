from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.services.db_bootstrap import bootstrap_db

# routers
from backend.routes.predict import router as predict_router
from backend.routes.actual_result import router as actual_router
from backend.routes.kpi_match import router as kpi_match_router
from backend.routes.kpi_summary import router as kpi_summary_router
from backend.routes.dashboard import router as dashboard_router
from backend.routes.kpi_report import router as kpi_report_router
from backend.routes.ui_results import router as ui_results_router
from backend.routes.kpi_status import router as kpi_status_router
from backend.routes.kpi_alert import router as kpi_alert_router


app = FastAPI(title="Race KPI Backend", version="0.1.0")

# CORS (필요시 유지)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔴 핵심: 서버 시작 시 DB 부트스트랩
@app.on_event("startup")
def on_startup():
    bootstrap_db()

# routers (중복 prefix 없이!)
app.include_router(predict_router)
app.include_router(actual_router)
app.include_router(kpi_match_router)
app.include_router(kpi_summary_router)
app.include_router(dashboard_router)
app.include_router(kpi_report_router)
app.include_router(ui_results_router)
app.include_router(kpi_status_router)
app.include_router(kpi_alert_router)

@app.get("/health")
def health():
    return {"status": "ok"}
