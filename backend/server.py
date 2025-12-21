from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.races import router as races_router
from routes.predict import router as predict_router
from routes.report import router as report_router
from routes.summary import router as summary_router
from routes.feedback import router as feedback_router
from routes.dashboard import router as dashboard_router

from scheduler import start_scheduler

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(races_router)
app.include_router(predict_router)
app.include_router(report_router)
app.include_router(summary_router)
app.include_router(feedback_router)
app.include_router(dashboard_router)

@app.on_event("startup")
def _startup():
    start_scheduler()

@app.get("/")
def root():
    return {"status": "backend-ok"}
