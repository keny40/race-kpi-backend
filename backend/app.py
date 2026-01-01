# backend/app.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# routers
from backend.routes.admin_metrics import router as admin_router
from backend.routes.mock import router as mock_router

# services
from backend.services.ops_scheduler import start_scheduler

app = FastAPI()

# =========================
# Middleware
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Static UI
# =========================
app.mount("/ui", StaticFiles(directory="backend/static", html=True), name="ui")

# =========================
# Routers
# =========================
app.include_router(admin_router)
app.include_router(mock_router)

# =========================
# Health Check
# =========================
@app.get("/health")
def health():
    return {"status": "ok"}

# =========================
# Startup Event
# =========================
@app.on_event("startup")
def startup():
    start_scheduler()
