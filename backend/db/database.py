from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./races.db"  # MySQL이면 mysql+pymysql://user:pw@host/dbname

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite용
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
