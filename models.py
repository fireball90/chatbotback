from sqlalchemy import Boolean, Column, Integer, String, Date
from database import Base

class Logs(Base):
    __tablename__ = 'logs'

    id=Column(Integer, primary_key = True)
    logid=Column(String(10))
    question=Column(String(500))
    answer=Column(String(1000))
    date=Column(Date)