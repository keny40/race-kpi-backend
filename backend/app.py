from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
import os

# 🔹 라우터 import
from backend.routes.predict import router as predict_router
from backend.routes.result import router as result_router

app = FastAPI(title="Race KPI Backend")

# ===== CORS =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

# ===== OPTIONS (preflight 강제 통과) =====
@app.options("/{path:path}")
async def options_handler(path: str, request: Request):
    return Response(status_code=200)

# ===== Root =====
@app.get("/")
def root():
    return {"status": "ok"}

# ===== Router 등록 (🔥 이 부분이 핵심) =====
print("✅ predict router loaded")
app.include_router(predict_router)

print("✅ result router loaded")
app.include_router(result_router)

# ===== Static =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

if os.path.isdir(STATIC_DIR):
    app.mount(
        "/static",
        StaticFiles(directory=STATIC_DIR, html=True),
        name="static"
    )
