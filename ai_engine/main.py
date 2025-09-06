from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from openai import OpenAI
import os, json, hashlib
from fastapi.responses import JSONResponse
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

# Import sibling module directly since this service runs as a top-level module (uvicorn main:app)
from vector_store import VectorStore, chunk_text

app = FastAPI(title="AI Engine")

# ----- Logging -----
AI_LOG_DIR = os.getenv("AI_LOG_DIR") or os.getenv("VECTOR_DB_DIR") or "/data/logs"
try:
    os.makedirs(AI_LOG_DIR, exist_ok=True)
except Exception:
    AI_LOG_DIR = "/data"

log_level = os.getenv("AI_LOG_LEVEL", "INFO").upper()
logger = logging.getLogger("ai_engine")
logger.setLevel(log_level)
_fmt = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
if not any(isinstance(h, (RotatingFileHandler, TimedRotatingFileHandler)) for h in logger.handlers):
    fh = TimedRotatingFileHandler(os.path.join(AI_LOG_DIR, 'ai_engine.log'), when='midnight', interval=1, backupCount=int(os.getenv('AI_LOG_BACKUPS', 7)))
    # Name rotated files by date: ai_engine.log.YYYY-MM-DD
    try:
        fh.suffix = "%Y-%m-%d"
    except Exception:
        pass
    fh.setFormatter(_fmt)
    logger.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setFormatter(_fmt)
    logger.addHandler(ch)

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


class PageChunk(BaseModel):
    page: int
    text: str


class IndexDocumentRequest(BaseModel):
    document_id: str
    title: Optional[str] = None
    text: Optional[str] = Field(None, description="Plaintext content to index")
    pages: Optional[List[PageChunk]] = Field(None, description="Optional per-page texts for precise page mapping")


def embed_texts(texts: List[str]) -> List[List[float]]:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")
    # simple retry on transient errors
    last_exc = None
    for _ in range(2):
        try:
            resp = client.embeddings.create(model=os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small"), input=texts)
            return [d.embedding for d in resp.data]
        except Exception as e:
            last_exc = e
    raise RuntimeError(f"embed_failed: {last_exc}")


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
    try:
        logger.info("index_document doc_id=%s title=%s pages=%s text_len=%s", req.document_id, (req.title or "")[:80], len(req.pages or []), len(req.text or ""))
    except Exception:
        pass
    items = []
    texts_to_embed: List[str] = []
    metas: List[Dict[str, Any]] = []

    if req.pages:
        # Build chunks per page and preserve page number in metadata
        for p in req.pages:
            for j, ch in enumerate(chunk_text(p.text or "", target_chars=1100)):
                texts_to_embed.append(ch)
                metas.append({
                    "document_id": req.document_id,
                    "title": req.title,
                    "chunk": j,
                    "page": int(p.page or 0) if p.page else None,
                })
    elif req.text:
        for j, ch in enumerate(chunk_text(req.text or "", target_chars=1200)):
            texts_to_embed.append(ch)
            metas.append({
                "document_id": req.document_id,
                "title": req.title,
                "chunk": j,
            })
    else:
        return JSONResponse({"ok": False, "error": "no_content", "detail": "Provide text or pages"}, status_code=400)

    try:
        embeds = embed_texts(texts_to_embed)
    except Exception as e:
        logger.exception("index_document embed_failed doc_id=%s error=%s", req.document_id, e)
        return JSONResponse({"ok": False, "error": "embed_failed", "detail": str(e)}, status_code=502)

    for i, (text, emb, meta) in enumerate(zip(texts_to_embed, embeds, metas)):
        # ensure unique id across doc
        uid = hashlib.sha1(f"{req.document_id}:{meta.get('page') or 0}:{meta.get('chunk') or i}".encode("utf-8")).hexdigest()
        items.append({"id": uid, "content": text, "metadata": meta, "embedding": emb})
    store.add_many(items)
    logger.info("index_document stored doc_id=%s chunks=%s", req.document_id, len(items))
    return {"ok": True, "chunks": len(items)}


class UnindexRequest(BaseModel):
    document_id: str

@app.post("/unindex_document")
def unindex_document(req: UnindexRequest):
    try:
        removed = store.delete_by_document_id(req.document_id)
        logger.info("unindex_document doc_id=%s removed=%s", req.document_id, removed)
        return {"ok": True, "removed": removed}
    except Exception as e:
        logger.exception("unindex_document failed doc_id=%s error=%s", req.document_id, e)
        return JSONResponse({"ok": False, "error": "unindex_failed", "detail": str(e)}, status_code=500)


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    try:
        text = content.decode("utf-8", errors="ignore")
    except Exception:
        text = ""
    doc_id = file.filename
    try:
        logger.info("upload name=%s size=%s", file.filename, len(content or b""))
    except Exception:
        pass
    index_document(IndexDocumentRequest(document_id=doc_id, title=file.filename, text=text))
    return {"message": "uploaded", "document_id": doc_id}


@app.post("/ask")
def ask(req: AskRequest):
    q = (req.question or "").strip()
    if not q:
        return {"answer": "", "sources": []}
    logger.info("ask len=%s top_k=%s", len(q), req.top_k)
    q_emb = embed_texts([q])[0]
    matches = store.query(q_emb, top_k=max(1, min(25, req.top_k * 3)))
    # Collapse citations by document (keep best score); cap to req.top_k unique
    best_by_doc = {}
    for m in matches:
        meta = (m.get("metadata") or {})
        doc_id = meta.get("document_id")
        if not doc_id:
            continue
        prev = best_by_doc.get(doc_id)
        if (not prev) or (m.get("score", 0) > prev.get("score", 0)):
            best_by_doc[doc_id] = {
                "title": meta.get("title"),
                "document_id": doc_id,
                # Expose chunk index as page-ish indicator (1-based)
                "page": (meta.get("chunk") + 1) if isinstance(meta.get("chunk"), int) else None,
                "url": meta.get("url") or meta.get("source_url"),
                "score": float(m.get("score") or 0),
                "chunk": meta.get("chunk"),
                "excerpt": (m.get("content") or "").strip()[:220],
            }
    # Sort by score desc and limit to requested top_k (for chips / fallback)
    citations = sorted(best_by_doc.values(), key=lambda x: x.get("score", 0), reverse=True)[: max(1, req.top_k)]
    try:
        answer = answer_with_openai(q, matches)
    except Exception as e:
        logger.exception("ask openai_failed error=%s", e)
        return JSONResponse({"ok": False, "error": "openai_failed", "detail": str(e)}, status_code=502)
    # Build inline refs map aligned to [n] citations used by the model
    inline_refs = {}
    for i, m in enumerate(matches, 1):
        meta = (m.get("metadata") or {})
        inline_refs[str(i)] = {
            "title": meta.get("title"),
            "document_id": meta.get("document_id"),
            "page": (meta.get("page") if isinstance(meta.get("page"), int) else ((meta.get("chunk") + 1) if isinstance(meta.get("chunk"), int) else None)),
            "url": meta.get("url") or meta.get("source_url"),
        }
    out = {"answer": answer, "inline_refs": inline_refs}
    if req.with_sources:
        out["sources"] = citations
    return out
@app.get("/health")
def health():
    return {"ok": True}


class EmbedRequest(BaseModel):
    texts: List[str]
    model: str | None = None

@app.post("/embed")
def embed(req: EmbedRequest):
    model = req.model or os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
    if not req.texts:
        return {"vectors": []}
    # Use our helper; override model via env for now
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")
    logger.info("embed count=%s model=%s", len(req.texts), model)
    resp = client.embeddings.create(model=model, input=req.texts)
    return {"vectors": [d.embedding for d in resp.data], "model": model}


class RerankRequest(BaseModel):
    query: str
    passages: List[str]

@app.post("/rerank")
def rerank(req: RerankRequest):
    # Minimal stub: preserve order with trivial scores
    try:
        logger.info("rerank passages=%s", len(req.passages or []))
    except Exception:
        pass
    return {"results": [{"text": p, "score": 1.0 - (i * 0.01)} for i, p in enumerate(req.passages)]}
