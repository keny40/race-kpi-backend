import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

# ===============================
# BASE DIR
# ===============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ===============================
# APP INIT
# ===============================
app = FastAPI(title="Race KPI Backend")

# ===============================
# CORS
# ===============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================
# ROUTERS (중복 없이)
# ===============================
from backend.routes.predict import router as predict_router
from backend.routes.actual_result import router as actual_router
from backend.routes.kpi_summary import router as kpi_summary_router
from backend.routes.kpi_match import router as kpi_match_router
from backend.routes.kpi_alert import router as kpi_alert_router
from backend.routes.kpi_status import router as kpi_status_router
from backend.routes.admin import router as admin_router
from backend.routes.admin_auth import router as admin_auth_router
from backend.routes.admin_control import router as admin_control_router

# ===============================
# ROOT → ADMIN UI
# ===============================
@app.get("/")
def root():
    return RedirectResponse(url="/admin/index.html")

# ===============================
# HEALTH CHECK
# ===============================
@app.get("/health")
def health():
    return {"status": "ok"}

# ===============================
# API ROUTERS
# ===============================
app.include_router(predict_router)
app.include_router(actual_router)

app.include_router(kpi_summary_router)
app.include_router(kpi_match_router)
app.include_router(kpi_alert_router)
app.include_router(kpi_status_router)

app.include_router(admin_router)
app.include_router(admin_auth_router)
app.include_router(admin_control_router)

# ===============================
# STATIC FILES (정답)
# ===============================
app.mount(
    "/admin",
    StaticFiles(
        directory=os.path.join(BASE_DIR, "static", "admin"),
        html=True
    ),
    name="admin",
)

app.mount(
    "/static",
    StaticFiles(
        directory=os.path.join(BASE_DIR, "static")
    ),
    name="static",
)
