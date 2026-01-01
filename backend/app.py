# backend/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import os

from backend.routes.admin_metrics import router as admin_api_router
from backend.routes.metrics import router as metrics_router
from backend.services.health_watch import start_watch
from backend.routes.sse import router as sse_router
from backend.services.ops_scheduler import start as start_scheduler
from backend.routes.mock import router as mock_router


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
ADMIN_STATIC_DIR = os.path.join(STATIC_DIR, "admin")

app = FastAPI(title="Ops & Risk Control Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API
app.include_router(admin_api_router)
app.include_router(metrics_router)
app.include_router(sse_router)
app.include_router(mock_router)

# 1️⃣ ROOT → ADMIN redirect
@app.get("/")
def root_redirect():
    return RedirectResponse(url="/admin/")

# 2️⃣ Health / Ready
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    return {"ready": True}
    
@app.on_event("startup")
def startup():
    start_watch("http://127.0.0.1:8000/health")
    
    @app.on_event("startup")
def startup():
    start_scheduler()

# Static UIs
app.mount("/admin", StaticFiles(directory=ADMIN_STATIC_DIR, html=True), name="admin-ui")
app.mount("/ui", StaticFiles(directory=STATIC_DIR, html=True), name="ui")
