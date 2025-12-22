from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

# ===== CORS (테스트/연동 단계 기준) =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

# ===== 전역 OPTIONS (preflight 강제 통과) =====
@app.options("/{path:path}")
async def options_handler(path: str, request: Request):
    return Response(status_code=200)

# ===== 루트 =====
@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "race-kpi-backend"
    }

# ===== 라우터 등록 =====
from backend.routes.kpi_matrix import router as kpi_matrix_router
from backend.routes.strategy_state import router as strategy_state_router
from backend.routes.kpi_report import router as kpi_report_router
from backend.routes.kpi_testdata import router as kpi_testdata_router
from backend.routes.kpi_summary import router as kpi_summary_router
from backend.routes.kpi_trend import router as kpi_trend_router

app.include_router(kpi_matrix_router)
app.include_router(strategy_state_router)
app.include_router(kpi_report_router)
app.include_router(kpi_testdata_router)
app.include_router(kpi_summary_router)
app.include_router(kpi_trend_router)

# ===== 정적 파일 (존재할 때만 mount: Render 안전) =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

if os.path.isdir(STATIC_DIR):
    app.mount(
        "/static",
        StaticFiles(directory=STATIC_DIR, html=True),
        name="static"
    )
