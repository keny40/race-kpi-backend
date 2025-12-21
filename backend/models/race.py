from sqlalchemy import Column, Integer, String, Date
from db.database import Base

class Race(Base):
    __tablename__ = "races"

    id = Column(Integer, primary_key=True, index=True)
    race_date = Column(Date, index=True)
    race_no = Column(Integer)
    title = Column(String)
