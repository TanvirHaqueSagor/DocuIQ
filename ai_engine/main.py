from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from openai import OpenAI
import os, json, hashlib

# Import sibling module directly since this service runs as a top-level module (uvicorn main:app)
from vector_store import VectorStore, chunk_text

app = FastAPI(title="AI Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
client = OpenAI(api_key=OPENAI_API_KEY or None)

DB_PATH = os.getenv("VECTOR_DB_PATH", os.path.join(os.path.dirname(__file__), "vector_store.sqlite3"))
store = VectorStore(DB_PATH)


class AskRequest(BaseModel):
    question: str
    top_k: int = 5
    with_sources: bool = True


class IndexDocumentRequest(BaseModel):
    document_id: str
    title: str | None = None
    text: str = Field(..., description="Plaintext content to index")


def embed_texts(texts: List[str]) -> List[List[float]]:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")
    resp = client.embeddings.create(model="text-embedding-3-small", input=texts)
    return [d.embedding for d in resp.data]


def answer_with_openai(question: str, context_chunks: List[Dict[str, Any]]) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")
    context = []
    for i, ch in enumerate(context_chunks, 1):
        meta = ch.get("metadata", {})
        doc_id = meta.get("document_id") or meta.get("documentId") or meta.get("doc_id")
        title = meta.get("title") or ""
        context.append(f"[Source {i}] doc={doc_id} title={title}\n{ch['content']}")
    ctx = "\n\n".join(context)
    sys = (
        "You are a helpful assistant answering questions strictly using the provided context. "
        "Cite sources inline like [1], [2] where relevant. If you are uncertain or the answer "
        "isn't in the context, say you don't know."
    )
    user = f"Question: {question}\n\nContext:\n{ctx}"
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()


@app.post("/index_document")
def index_document(req: IndexDocumentRequest):
    chunks = list(chunk_text(req.text, target_chars=1200))
    embeds = embed_texts(chunks)
    items = []
    for i, (text, emb) in enumerate(zip(chunks, embeds)):
        uid = hashlib.sha1(f"{req.document_id}:{i}".encode("utf-8")).hexdigest()
        meta = {"document_id": req.document_id, "title": req.title, "chunk": i}
        items.append({"id": uid, "content": text, "metadata": meta, "embedding": emb})
    store.add_many(items)
    return {"ok": True, "chunks": len(items)}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    try:
        text = content.decode("utf-8", errors="ignore")
    except Exception:
        text = ""
    doc_id = file.filename
    index_document(IndexDocumentRequest(document_id=doc_id, title=file.filename, text=text))
    return {"message": "uploaded", "document_id": doc_id}


@app.post("/ask")
def ask(req: AskRequest):
    q = (req.question or "").strip()
    if not q:
        return {"answer": "", "sources": []}
    q_emb = embed_texts([q])[0]
    matches = store.query(q_emb, top_k=max(1, min(10, req.top_k)))
    citations = [
        {
            "title": (m.get("metadata") or {}).get("title"),
            "document_id": (m.get("metadata") or {}).get("document_id"),
            "score": m.get("score"),
        }
        for m in matches
    ]
    answer = answer_with_openai(q, matches)
    out = {"answer": answer}
    if req.with_sources:
        out["sources"] = citations
    return out
@app.get("/health")
def health():
    return {"ok": True}
