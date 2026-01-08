from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# 1️⃣ FastAPI 앱 생성 (최상단)
app = FastAPI(title="Horse Race AI")

# 2️⃣ static 파일 마운트
app.mount(
    "/static",
    StaticFiles(directory="backend/static", html=True),
    name="static"
)

# 3️⃣ 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4️⃣ 라우터 import (Form / UploadFile 없는 것들만 기본 로딩)
from backend.routes.admin_pre_race_report import router as admin_pre_race_report_router
from backend.routes.admin_pre_race_summary import router as admin_pre_race_summary_router
from backend.routes.admin_pre_race_compare import router as admin_pre_race_compare_router
from backend.routes.admin_pre_race_rules import router as admin_pre_race_rules_router
from backend.routes.admin_pre_race_summary_stats import router as pre_race_summary_stats_router
from backend.routes.kpi_summary import router as kpi_summary_router
from backend.routes.admin_guard import router as admin_guard_router

# 5️⃣ 라우터 등록
app.include_router(kpi_summary_router)
app.include_router(admin_guard_router)

app.include_router(admin_pre_race_summary_router)
app.include_router(pre_race_summary_stats_router)

app.include_router(admin_pre_race_summary_router, prefix="/api/admin/pre-race")
app.include_router(admin_pre_race_rules_router, prefix="/api/admin/pre-race")
app.include_router(admin_pre_race_compare_router, prefix="/api/admin/pre-race")
app.include_router(admin_pre_race_report_router, prefix="/api/admin/pre-race")

# 6️⃣ Upload / multipart 라우터는 조건부 로딩 (Render 보호)
if os.getenv("ENABLE_UPLOAD", "0") == "1":
    from backend.routes.collect_upload import router as collect_upload_router
    app.include_router(collect_upload_router)

# 7️⃣ 서버 시작 시 스케줄러 자동 실행
from backend.services.pre_race_scheduler import start as start_pre_race_scheduler

@app.on_event("startup")
def startup_event():
    start_pre_race_scheduler()
