from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Annotated
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
import datetime


app = FastAPI()
models.Base.metadata.create_all(bind=engine)

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
    #MORE IF NEEDED
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

class PostLogBase(BaseModel):
    logid: str
    question: str

class PostBase(BaseModel):
    logid: str
    question: str
    answer:str
    date: datetime.datetime

class LogBase(BaseModel):
    answer:str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]


# GET

#GET ONE LOG
@app.get("/logs/{log_id}", status_code=status.HTTP_200_OK)
async def get_log(log_id: str, db: db_dependency):
    logs = db.query(models.Logs).filter(models.Logs.logid == log_id).first()
    if logs is None:
        raise HTTPException(status_code=404, detail="Log not found!")
    return logs

#GET ALL LOGS
@app.get("/all_logs/", status_code=status.HTTP_200_OK)
async def get_logs(db:db_dependency):
    logs = db.query(models.Logs).all()
    if logs is None:
        raise HTTPException(status_code=404, detail="There are no logs!")
    return logs

#GET ALL LOGID GROUPED BY LOGID
@app.get("/logs/", status_code=status.HTTP_200_OK)
async def get_log_ids(db: db_dependency):
    log_ids = db.query(models.Logs.logid).group_by(models.Logs.logid).all()
    if not log_ids:
        raise HTTPException(status_code=404, detail="There are no logs!")
    return [log_id[0] for log_id in log_ids]

#GET ALL LOGS FOR A LOG ID
@app.get("/all_logs/{log_id}", status_code=status.HTTP_200_OK)
async def get_logs_by_id(log_id: str, db: db_dependency):
    logs = db.query(models.Logs).filter(models.Logs.logid == log_id).all()
    if logs is None:
        raise HTTPException(status_code=404, detail="There are no logs!")
    return logs
# POST

#POST FULL LOG
@app.post("/logs-all/", status_code=status.HTTP_201_CREATED)
async def create_log(log: PostBase, db: db_dependency):
    db_log = models.Logs(**log.dict())
    db.add(db_log)
    db.commit()

