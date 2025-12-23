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

# static
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "backend" / "static"

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static"
)

# routers (❗ backend. 제거)
from routes.predict import router as predict_router
from routes.result_actual import router as result_router

app.include_router(predict_router)
app.include_router(result_router)

# root dashboard
@app.get("/", response_class=HTMLResponse)
def root():
    index_path = STATIC_DIR / "dashboard" / "index.html"
    return index_path.read_text(encoding="utf-8")

# health
@app.get("/health")
def health():
    return {"status": "ok"}
