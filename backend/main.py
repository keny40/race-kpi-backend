from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.predict import router as predict_router
from backend.routes.result_actual import router as result_actual_router
from backend.routes.result import router as result_router
from backend.routes.kpi_match import router as kpi_match_router
from backend.routes.ui_results import router as ui_results_router


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

# Routers
app.include_router(predict_router)
app.include_router(result_actual_router)
app.include_router(result_router)
app.include_router(kpi_match_router)
app.include_router(ui_results_router)


@app.get("/_debug")
def debug():
    return {
        "app": "RUNNING",
        "routers": [
            "predict",
            "result",
            "result_actual",
            "kpi_match",
            "ui_results"
        ]
    }


@app.get("/")
def health():
    return {"status": "ok"}
