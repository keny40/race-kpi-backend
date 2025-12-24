from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.predict import router as predict_router
from backend.routes.result_actual import router as result_actual_router

app = FastAPI(title="Race KPI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict_router)
app.include_router(result_actual_router)

@app.get("/")
def health():
    return {"status": "ok"}
