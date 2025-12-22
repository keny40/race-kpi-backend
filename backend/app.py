from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
import os

print("🚀 backend.app STARTED")

app = FastAPI(title="Race KPI Backend")

# ===== CORS =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

# ===== OPTIONS =====
@app.options("/{path:path}")
async def options_handler(path: str, request: Request):
    return Response(status_code=200)

# ===== Root =====
@app.get("/")
def root():
    return {"status": "ok"}

# ===== Router imports (🔥 여기서 확인) =====
try:
    from backend.routes.predict import router as predict_router
    print("✅ predict_router imported")
except Exception as e:
    print("❌ predict_router import FAILED:", e)

try:
    from backend.routes.result import router as result_router
    print("✅ result_router imported")
except Exception as e:
    print("❌ result_router import FAILED:", e)

# ===== Router include =====
try:
    app.include_router(predict_router)
    print("✅ predict_router included")
except Exception as e:
    print("❌ predict_router include FAILED:", e)

try:
    app.include_router(result_router)
    print("✅ result_router included")
except Exception as e:
    print("❌ result_router include FAILED:", e)

# ===== Static =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

if os.path.isdir(STATIC_DIR):
    app.mount(
        "/static",
        StaticFiles(directory=STATIC_DIR, html=True),
        name="static"
    )
