from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from typing import List
import os

app = FastAPI()
DB = {}

class AskRequest(BaseModel):
    question: str
    document_id: str

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode('utf-8')  # For demo only
    DB[file.filename] = text
    return {"message": "uploaded", "document_id": file.filename}

@app.post("/ask")
def ask(query: AskRequest):
    doc = DB.get(query.document_id, "")
    answer = query.question in doc
    return {"answer": f"Found: {answer}", "source": query.document_id}
