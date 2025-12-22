from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory="backend/static", html=True),
    name="static"
)

# ===== CORS (단 한 번만, 이 설정이 정답) =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # 테스트 단계
    allow_methods=["*"],          # OPTIONS 포함
    allow_headers=["*"],          # Content-Type 포함
    allow_credentials=False,      # origin=null 대응 (중요)
)

# ===== 전역 OPTIONS 핸들러 (preflight 강제 통과) =====
@app.options("/{path:path}")
async def options_handler(path: str, request: Request):
    return Response(status_code=200)

# ===== 루트 엔드포인트 =====
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

# ===== 관리자 정적 페이지 =====
app.mount(
    "/admin",
    StaticFiles(directory="backend/admin", html=True),
    name="admin"
)
