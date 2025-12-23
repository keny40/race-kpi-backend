from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI(
    title="Race KPI Backend",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 프로젝트 루트 기준 절대경로
BASE_DIR = Path(__file__).resolve().parent
DASHBOARD_HTML = BASE_DIR / "backend" / "static" / "dashboard" / "index.html"

# static mount
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "backend" / "static"),
    name="static"
)

# API routers
from backend.routes.predict import router as predict_router
from backend.routes.result_actual import router as result_router

app.include_router(predict_router)
app.include_router(result_router)

# ROOT → 대시보드
@app.get("/", response_class=HTMLResponse)
def root():
    return DASHBOARD_HTML.read_text(encoding="utf-8")

# health check
@app.get("/health")
def health():
    return {"status": "ok"}
