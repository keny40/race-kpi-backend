from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

# === routers ===
from backend.routes.predict import router as predict_router
from backend.routes.actual_result import router as actual_router
from backend.routes.kpi_summary import router as kpi_summary_router
from backend.routes.kpi_match import router as kpi_match_router
from backend.routes.kpi_alert import router as kpi_alert_router
from backend.routes.kpi_status import router as kpi_status_router
from backend.routes.admin import router as admin_router

# === app ===
app = FastAPI(title="Race KPI Backend")

# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === root → admin redirect ===
@app.get("/")
def root():
    return RedirectResponse(url="/admin")

# === health check ===
@app.get("/health")
def health():
    return {"status": "ok"}

# === include routers ===
app.include_router(predict_router)
app.include_router(actual_router)

app.include_router(kpi_summary_router)
app.include_router(kpi_match_router)
app.include_router(kpi_alert_router)
app.include_router(kpi_status_router)

app.include_router(admin_router)
