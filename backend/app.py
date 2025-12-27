from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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
from backend.routes.admin import router as admin_router

from backend.scheduler import start_scheduler
import os


app = FastAPI(
    title="Race KPI Backend",
    version="0.1.0"
)

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Startup
# -----------------------------
@app.on_event("startup")
def startup():
    bootstrap_db()
    start_scheduler()

# -----------------------------
# Routers (API)
# -----------------------------
app.include_router(predict_router)
app.include_router(actual_router)
app.include_router(kpi_match_router)
app.include_router(kpi_summary_router)
app.include_router(dashboard_router)
app.include_router(kpi_report_router)
app.include_router(ui_results_router)
app.include_router(kpi_status_router)
app.include_router(kpi_alert_router)
app.include_router(admin_router)

# -----------------------------
# 🔑 관리자 UI (StaticFiles)
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # backend/
ADMIN_STATIC = os.path.join(BASE_DIR, "static", "admin")

app.mount(
    "/admin",
    StaticFiles(directory=ADMIN_STATIC, html=True),
    name="admin"
)

# -----------------------------
# Health
# -----------------------------
@app.get("/health")
def health():
    return {"status": "ok"}
