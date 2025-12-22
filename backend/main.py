from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.scheduler import start_scheduler
from backend.services.db_bootstrap import bootstrap_db

# 🔹 라우터 import
from backend.routes.predict import router as predict_router
from backend.routes.result import router as result_router   # 🔴 핵심

app = FastAPI(title="Race Result Ingest API")

@app.on_event("startup")
def startup():
    bootstrap_db()
    start_scheduler()

# ===== API Routers =====
app.include_router(predict_router)        # /api/predict
app.include_router(result_router)         # /api/result/actual 🔴 이 줄이 핵심

# ===== Root =====
@app.get("/")
def root():
    return {"status": "ok"}

# ===== Static (필요 시) =====
app.mount(
    "/frontend",
    StaticFiles(directory="frontend"),
    name="frontend"
)
