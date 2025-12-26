from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# === Predict / Result ===
from backend.routes.predict import router as predict_router
from backend.routes.actual_result import router as actual_result_router

# === KPI ===
from backend.routes.kpi_match import router as kpi_match_router
from backend.routes.kpi_summary import router as kpi_summary_router

# === UI ===
from backend.routes.dashboard import router as dashboard_router
from backend.routes.kpi_report import router as kpi_report_router
from backend.routes.ui_results import router as ui_results_router

app = FastAPI(
    title="Race KPI Backend",
    version="0.1.0"
)

# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === API Routers ===
app.include_router(predict_router)
app.include_router(actual_result_router)

app.include_router(kpi_match_router, prefix="/api/kpi", tags=["kpi"])
app.include_router(kpi_summary_router, prefix="/api/kpi", tags=["kpi"])

# === UI Routers (중요: prefix /ui로 설정) ===
app.include_router(ui_results_router, prefix="/ui", tags=["ui"])
app.include_router(kpi_report_router, prefix="/ui", tags=["ui"])
app.include_router(dashboard_router, prefix="/ui", tags=["ui"])

# === Health / Debug ===
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/_debug")
def debug():
    return {
        "service": "race-kpi-backend",
        "status": "running"
    }
