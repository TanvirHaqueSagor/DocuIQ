from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Set
from openai import OpenAI
import os, json, hashlib, re
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
    source_type: Optional[str] = Field(None, description="Source kind (pdf, web, drive, etc.)")
    origin_url: Optional[str] = Field(None, description="Original URL if available for citation deep links")


class Citation(BaseModel):
    citation_id: str
    doc_id: str
    doc_title: Optional[str] = None
    source_type: Optional[str] = None
    page: Optional[int] = None
    chunk_id: Optional[str] = None
    chunk_index: Optional[int] = None
    score: Optional[float] = None
    snippet: str
    url: Optional[str] = None


def _clean_snippet(text: str, limit: int = 420) -> str:
    raw = ' '.join((text or '').split())
    if not raw:
        return ''
    parts = re.split(r'(?<=[.!?])\s+', raw)
    snippet = ' '.join(parts[:3]) if parts and len(' '.join(parts[:3])) <= limit else raw[:limit]
    return snippet.strip()


def _guess_source_type(meta: Dict[str, Any]) -> Optional[str]:
    st = meta.get("source_type") or meta.get("kind")
    if st:
        return str(st)
    title = (meta.get("title") or "").lower()
    if "web" in title:
        return "web"
    return None


def _build_view_path(doc_id: str, page: Optional[int], meta: Dict[str, Any]) -> Optional[str]:
    url = meta.get("view_url") or meta.get("url") or meta.get("origin_url") or meta.get("source_url")
    if url:
        return url
    if not doc_id:
        return None
    if page:
        return f"/documents/{doc_id}?p={page}"
    return f"/documents/{doc_id}"


def _coerce_page(meta: Dict[str, Any]) -> Optional[int]:
    page = meta.get("page")
    if isinstance(page, int) and page > 0:
        return page
    chunk = meta.get("chunk")
    if isinstance(chunk, int):
        return chunk + 1
    return None


def _build_citations(matches: List[Dict[str, Any]], limit: int) -> List[Citation]:
    citations: List[Citation] = []
    seen_chunks: Set[str] = set()
    for match in matches:
        meta = match.get("metadata") or {}
        doc_id = str(meta.get("document_id") or meta.get("documentId") or meta.get("doc_id") or "").strip()
        if not doc_id:
            continue
        chunk_idx = meta.get("chunk")
        chunk_id = meta.get("chunk_id") or f"{doc_id}:{meta.get('page') or 0}:{chunk_idx if chunk_idx is not None else ''}"
        if chunk_id in seen_chunks:
            continue
        seen_chunks.add(chunk_id)
        page = _coerce_page(meta)
        snippet = _clean_snippet(match.get("content") or "")
        citation = Citation(
            citation_id=f"S{len(citations) + 1}",
            doc_id=doc_id,
            doc_title=meta.get("title"),
            source_type=_guess_source_type(meta) or (match.get("metadata") or {}).get("source_type"),
            page=page,
            chunk_id=str(chunk_id),
            chunk_index=chunk_idx if isinstance(chunk_idx, int) else None,
            score=float(match.get("score") or 0.0),
            snippet=snippet,
            url=_build_view_path(doc_id, page, meta),
        )
        citations.append(citation)
        if len(citations) >= limit:
            break
    return citations


def _render_sources_for_prompt(citations: List[Citation]) -> str:
    lines = []
    for c in citations:
        lines.append(
            f"[{c.citation_id}] Document: {c.doc_title or c.doc_id}\n"
            f"Page: {c.page or 'unknown'} | Type: {c.source_type or 'document'}\n"
            f"Snippet: {c.snippet}"
        )
    return "\n\n".join(lines)


def _extract_json_block(text: str) -> Dict[str, Any]:
    if not text:
        return {}
    snippet = text.strip()
    fenced_match = re.search(r"```json(.*?)```", snippet, flags=re.DOTALL | re.IGNORECASE)
    if fenced_match:
        snippet = fenced_match.group(1).strip()
    try:
        return json.loads(snippet)
    except Exception:
        pass
    start = snippet.find("{")
    end = snippet.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(snippet[start : end + 1])
        except Exception:
            return {}
    return {}


def _extract_markers(answer: str) -> List[str]:
    if not answer:
        return []
    ids = re.findall(r"\[S(\d+)]", answer)
    out = []
    for marker in ids:
        cid = f"S{marker}"
        if cid not in out:
            out.append(cid)
    return out


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


def answer_with_openai(question: str, citations: List[Citation]) -> Dict[str, Any]:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")
    if not citations:
        return {"answer": "", "citations_used": []}
    ctx = _render_sources_for_prompt(citations)
    sys = (
        "You are DocuIQ's enterprise research assistant. "
        "Answer using only the supplied sources. "
        "Every factual statement must reference a citation marker like [S1]. "
        "If the information isn't present, state that it was not found."
    )
    format_hint = (
        "Respond ONLY with valid JSON using this schema:\n"
        "{\n"
        '  "answer": "<full narrative with [S#] markers>",\n'
        '  "bullets": ["optional bullet list"],\n'
        '  "table": {"headers": [], "rows": []},\n'
        '  "citations_used": ["S1","S2"]\n'
        "}\n"
        "Omit bullets/table if not needed but keep the keys."
    )
    user = f"Question: {question}\n\nSources:\n{ctx}\n\n{format_hint}"
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": user},
        ],
        temperature=0.1,
    )
    raw = resp.choices[0].message.content.strip()
    parsed = _extract_json_block(raw) or {}
    if "answer" not in parsed:
        parsed["answer"] = raw
    if "citations_used" not in parsed:
        parsed["citations_used"] = _extract_markers(parsed.get("answer", ""))
    return parsed


@app.post("/index_document")
def index_document(req: IndexDocumentRequest):
    try:
        logger.info("index_document doc_id=%s title=%s pages=%s text_len=%s", req.document_id, (req.title or "")[:80], len(req.pages or []), len(req.text or ""))
    except Exception:
        pass
    items = []
    texts_to_embed: List[str] = []
    metas: List[Dict[str, Any]] = []

    source_type = (req.source_type or "").strip().lower() or None
    origin_url = (req.origin_url or "").strip() or None
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
                    "chunk_id": f"{req.document_id}:p{p.page or 0}:c{j}",
                    "source_type": source_type,
                    "origin_url": origin_url,
                })
    elif req.text:
        for j, ch in enumerate(chunk_text(req.text or "", target_chars=1200)):
            texts_to_embed.append(ch)
            metas.append({
                "document_id": req.document_id,
                "title": req.title,
                "chunk": j,
                "chunk_id": f"{req.document_id}:c{j}",
                "source_type": source_type,
                "origin_url": origin_url,
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


class ClearAllResponse(BaseModel):
    removed: int

@app.post("/admin/clear_all")
def clear_all_vectors() -> ClearAllResponse:
    try:
        removed = store.clear_all()
        logger.info("admin.clear_all removed=%s", removed)
        return {"removed": int(removed)}
    except Exception as e:
        logger.exception("admin.clear_all failed error=%s", e)
        return JSONResponse({"ok": False, "error": "clear_failed", "detail": str(e)}, status_code=500)


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
        return {"answer": "", "citations": [], "inline_refs": {}}
    logger.info("ask len=%s top_k=%s", len(q), req.top_k)
    q_emb = embed_texts([q])[0]
    max_matches = max(3, min(40, req.top_k * 4))
    matches = store.query(q_emb, top_k=max_matches)
    if not matches:
        return {"answer": "", "citations": [], "inline_refs": {}}
    context_limit = max(1, min(len(matches), max(3, req.top_k * 2)))
    context_matches = matches[:context_limit]
    citations = _build_citations(context_matches, limit=context_limit)
    if not citations:
        citations = _build_citations(matches, limit=max(1, req.top_k))
    for c in citations:
        try:
            logger.info("ask.retrieval doc=%s page=%s score=%.3f chunk=%s", c.doc_id, c.page, c.score or 0.0, c.chunk_id)
        except Exception:
            pass
    try:
        llm = answer_with_openai(q, citations)
    except Exception as e:
        logger.exception("ask openai_failed error=%s", e)
        return JSONResponse({"ok": False, "error": "openai_failed", "detail": str(e)}, status_code=502)
    answer_text = (llm.get("answer") or "").strip()
    cited_ids = llm.get("citations_used") or _extract_markers(answer_text) or []
    cite_map = {c.citation_id: c.dict() for c in citations}
    ordered_used = [cid for cid in cited_ids if cid in cite_map]
    if not ordered_used:
        ordered_used = [c.citation_id for c in citations[: req.top_k]]
    used_citations = [cite_map[cid] for cid in ordered_used if cid in cite_map]
    inline_refs = cite_map
    blocks = []
    bullets = llm.get("bullets") or []
    if isinstance(bullets, list) and bullets:
        blocks.append({"type": "bullets", "items": bullets})
    table = llm.get("table")
    if isinstance(table, dict) and table.get("headers") and table.get("rows"):
        blocks.append({"type": "table", "headers": table.get("headers"), "rows": table.get("rows")})
    out = {
        "answer": answer_text,
        "citations": used_citations if req.with_sources else [],
        "inline_refs": inline_refs,
        "blocks": blocks,
    }
    if req.with_sources:
        out["all_citations"] = list(cite_map.values())
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
