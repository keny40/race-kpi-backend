from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from datetime import date

# DB
from db.database import Base, engine, SessionLocal
from models.race import Race

# KRA scraping
from utils.kra_scraper import fetch_today_races

# 테이블 자동 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Race Predictor Backend", version="0.2.0")

# DB 세션 주입
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------------
# Health Check
# -------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# -------------------------------
# 1) DB 기반 오늘의 경주 조회
# -------------------------------
@app.get("/races/today")
def get_today_races(db: Session = Depends(get_db)):
    today = date.today()
    races = db.query(Race).filter(Race.race_date == today).all()
    return races


# -------------------------------
# 2) KRA 실시간 스크래핑 API
# -------------------------------
@app.get("/kra/today")
def get_kra_today():
    return fetch_today_races()


# -------------------------------
# 3) 홈
# -------------------------------
@app.get("/")
def home():
    return {"message": "Race Predictor Backend Running"}


# -------------------------------
# 4) 예측 엔드포인트 (기존 모델 유지)
# -------------------------------
from models.input_model import InputModel
from ai.predictor import predict_proba  # AI 예측 모듈

@app.post("/predict")
def predict_race(data: InputModel):
    result = predict_proba(data.dict())
    return {"prediction": result}
