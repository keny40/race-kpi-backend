from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
import os


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

@app.options("/{path:path}")
async def options_handler(path: str, request: Request):
    return Response(status_code=200)

@app.get("/")
def root():
    return {"status": "ok"}

# 🔴 라우터 전부 임시 비활성화
# from backend.routes.kpi_matrix import router as kpi_matrix_router
# ...
# app.include_router(...)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

if os.path.isdir(STATIC_DIR):
    app.mount(
        "/static",
        StaticFiles(directory=STATIC_DIR, html=True),
        name="static"
    )
