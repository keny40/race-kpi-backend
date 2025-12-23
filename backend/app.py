from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# === FastAPI app ===
app = FastAPI(
    title="Race KPI Backend",
    version="0.1.0"
)

# === CORS (프론트/외부 호출 대비) ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Static files (dashboard) ===
app.mount(
    "/static",
    StaticFiles(directory="backend/static"),
    name="static"
)

# === ROUTES IMPORT ===
from backend.routes.predict import router as predict_router
from backend.routes.result_actual import router as result_router

# KPI / 기타 라우터가 있다면 유지
try:
    from backend.routes.kpi_report import router as kpi_report_router
    from backend.routes.kpi_summary import router as kpi_summary_router
    from backend.routes.kpi_trend import router as kpi_trend_router

    app.include_router(kpi_report_router)
    app.include_router(kpi_summary_router)
    app.include_router(kpi_trend_router)
except Exception:
    pass

app.include_router(predict_router)
app.include_router(result_router)

# === ROOT: 대시보드 화면 ===
@app.get("/", response_class=HTMLResponse)
def root():
    try:
        with open("backend/static/dashboard/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(
            "<h2>dashboard/index.html not found</h2>",
            status_code=500
        )

# === Health check (Render용) ===
@app.get("/health")
def health():
    return {"status": "ok"}

# === OPTIONS handler (CORS preflight 안전장치) ===
@app.options("/{path:path}")
def options_handler(path: str):
    return JSONResponse(content={"ok": True})
