from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI(
    title="Race KPI Backend",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === BASE PATH ===
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DASHBOARD_HTML = STATIC_DIR / "dashboard" / "index.html"

# static mount
app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)

# === API routers ===
from backend.routes.predict import router as predict_router
from backend.routes.result_actual import router as result_router

app.include_router(predict_router)
app.include_router(result_router)

# === ROOT: dashboard ===
@app.get("/", response_class=HTMLResponse)
def root():
    if not DASHBOARD_HTML.exists():
        return HTMLResponse(
            f"<h1>Dashboard not found</h1><pre>{DASHBOARD_HTML}</pre>",
            status_code=500,
        )
    return DASHBOARD_HTML.read_text(encoding="utf-8")

# health check
@app.get("/health")
def health():
    return {"status": "ok"}
