from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Annotated
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
import datetime

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain import OpenAI
from langchain.chains import RetrievalQA
from langchain.document_loaders import DirectoryLoader
import magic
import os
import nltk


#result['result']
#print(result['result'])

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

openai_api_key = os.getenv("OPENAI_API_KEY", "apikey")

loader = DirectoryLoader('data', glob='**/*.txt')
documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
texts = text_splitter.split_documents(documents)

embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
docsearch = FAISS.from_documents(texts, embeddings)

llm = OpenAI(openai_api_key=openai_api_key)

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

#POST TRY
@app.post("/logs/", status_code=status.HTTP_201_CREATED)
async def create_logs(log: PostLogBase, db: db_dependency):
    time = datetime.datetime.utcnow()
    date = time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    logid = log.logid
    qa = RetrievalQA.from_chain_type(llm=llm,
                                chain_type="stuff",
                                retriever=docsearch.as_retriever(),
                                )
    query = log.question
    result = qa({"query": query})
    answer = result['result']
    db_log = models.Logs(logid=logid, question=query, answer = answer, date = date)
    db.add(db_log)
    db.commit()
    return answer
