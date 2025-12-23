from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend.routes.predict import router as predict_router
from backend.routes.result_actual import router as result_router

app = FastAPI(
    title="Race KPI Backend",
    version="0.1.0"
)

# ✅ 정적 파일 마운트
app.mount(
    "/static",
    StaticFiles(directory="backend/static"),
    name="static"
)

# ✅ 루트에 대시보드 HTML 연결
@app.get("/", response_class=HTMLResponse)
def root():
    with open("backend/static/dashboard/index.html", "r", encoding="utf-8") as f:
        return f.read()

# ✅ 기존 API 라우터
app.include_router(predict_router)
app.include_router(result_router)
