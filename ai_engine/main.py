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
    meta: Optional[Dict[str, Any]] = Field(None, description="Optional per-page metadata (e.g., url, anchors)")


class Fragment(BaseModel):
    text: str
    page: Optional[int] = None
    url: Optional[str] = None
    message_id: Optional[str] = None
    thread_id: Optional[str] = None
    ts: Optional[str] = None
    table: Optional[str] = None
    row_id: Optional[str] = None
    column: Optional[str] = None
    chunk_id: Optional[str] = None
    source_type: Optional[str] = None
    doc_title: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


class IndexDocumentRequest(BaseModel):
    document_id: str
    title: Optional[str] = None
    doc_title: Optional[str] = Field(None, description="Optional human-readable title/subject")
    text: Optional[str] = Field(None, description="Plaintext content to index")
    pages: Optional[List[PageChunk]] = Field(None, description="Optional per-page texts for precise page mapping")
    fragments: Optional[List[Fragment]] = Field(None, description="Optional fully-specified fragments with metadata")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Base metadata to attach to every chunk (location, provider, etc.)")
    source_type: Optional[str] = Field(None, description="Source kind (pdf, web, drive, etc.)")
    origin_url: Optional[str] = Field(None, description="Original URL if available for citation deep links")


class Citation(BaseModel):
    id: str
    citation_id: Optional[str] = None
    doc_id: str
    doc_title: Optional[str] = None
    source_type: str = "document"
    snippet: str
    score: Optional[float] = None
    
    # Location metadata
    page: Optional[int] = None
    url: Optional[str] = None
    message_id: Optional[str] = None
    thread_id: Optional[str] = None
    ts: Optional[str] = None
    table: Optional[str] = None
    row_id: Optional[str] = None
    column: Optional[str] = None
    
    # Internal/Extra
    chunk_id: Optional[str] = None
    chunk_index: Optional[int] = None
    extra: Optional[Dict[str, Any]] = None


def _clean_snippet(text: str, limit: int = 420) -> str:
    raw = text or ""
    if not raw:
        return ""
    if len(raw) <= limit:
        return raw
    # Keep a direct substring of the original text; prefer a sentence boundary within limit.
    boundary = max(raw.rfind(". ", 0, limit), raw.rfind("! ", 0, limit), raw.rfind("? ", 0, limit))
    if boundary != -1 and boundary + 1 > 0:
        return raw[: boundary + 1]
    return raw[:limit]


def _normalize_source_type(meta: Dict[str, Any], fallback: Optional[str] = None) -> Optional[str]:
    st = meta.get("source_type") or meta.get("kind") or fallback
    if not st:
        return None
    val = str(st).strip().lower()
    aliases = {
        "drive": "gdrive",
        "google_drive": "gdrive",
        "google-drive": "gdrive",
        "google": "gdrive",
        "ms_teams": "teams",
        "share-point": "sharepoint",
        "one_drive": "onedrive",
    }
    val = aliases.get(val, val)
    allowed = {"pdf", "web", "email", "slack", "teams", "gdrive", "db", "document", "notion", "sharepoint", "onedrive"}
    if val in allowed:
        return val
    return val or None


def _resolve_url(doc_id: str, page: Optional[int], meta: Dict[str, Any]) -> Optional[str]:
    url = meta.get("url") or meta.get("view_url") or meta.get("origin_url") or meta.get("source_url")
    if url:
        return str(url)
    if not doc_id:
        return None
    # As a last resort, expose the internal viewer path
    if page:
        return f"/documents/{doc_id}?p={page}"
    return f"/documents/{doc_id}"


def _coerce_page(meta: Dict[str, Any]) -> Optional[int]:
    page = meta.get("page")
    if isinstance(page, int) and page > 0:
        return page
    return None


def _coerce_chunk_index(meta: Dict[str, Any]) -> Optional[int]:
    chunk = meta.get("chunk")
    if isinstance(chunk, int) and chunk >= 0:
        return chunk
    return None


def _serialize_citation(c: Citation) -> Dict[str, Any]:
    data = c.dict()
    cid = c.id or c.citation_id
    data["id"] = cid
    data["citation_id"] = cid
    data["citationId"] = cid
    data.setdefault("doc_title", c.doc_title)
    return data


def _build_citations(matches: List[Dict[str, Any]], limit: int) -> List[Citation]:
    citations: List[Citation] = []
    seen_chunks: Set[str] = set()
    for match in matches:
        meta = match.get("metadata") or {}
        doc_id = str(meta.get("document_id") or meta.get("documentId") or meta.get("doc_id") or "").strip()
        if not doc_id:
            continue
        chunk_idx = _coerce_chunk_index(meta)
        chunk_id = str(meta.get("chunk_id") or match.get("id") or f"{doc_id}:{meta.get('page') or 0}:{chunk_idx if chunk_idx is not None else ''}")
        if chunk_id in seen_chunks:
            continue
        seen_chunks.add(chunk_id)
        page = _coerce_page(meta)
        snippet = _clean_snippet(match.get("content") or "")
        source_type = _normalize_source_type(meta) or "document"
        title = meta.get("doc_title") or meta.get("title") or meta.get("subject") or doc_id
        known_keys = {
            "document_id",
            "doc_id",
            "docId",
            "doc_title",
            "title",
            "subject",
            "source_type",
            "kind",
            "page",
            "chunk",
            "chunk_id",
            "origin_url",
            "url",
            "view_url",
            "source_url",
            "message_id",
            "messageId",
            "thread_id",
            "threadId",
            "ts",
            "table",
            "row_id",
            "rowId",
            "column",
            "extra",
        }
        extra_from_meta = {}
        if isinstance(meta.get("extra"), dict):
            extra_from_meta.update({k: v for k, v in (meta.get("extra") or {}).items() if v is not None})
        for k, v in meta.items():
            if k in known_keys or v is None:
                continue
            if isinstance(v, (dict, list, str, int, float, bool)):
                extra_from_meta[k] = v
        row_id = meta.get("row_id") or meta.get("rowId")
        citation_id = f"S{len(citations) + 1}"
        citation = Citation(
            id=citation_id,
            citation_id=citation_id,
            doc_id=doc_id,
            doc_title=title,
            source_type=source_type,
            page=page,
            url=_resolve_url(doc_id, page, meta),
            message_id=meta.get("message_id") or meta.get("messageId"),
            thread_id=meta.get("thread_id") or meta.get("threadId"),
            ts=str(meta.get("ts")) if meta.get("ts") is not None else None,
            table=meta.get("table"),
            row_id=str(row_id) if row_id is not None else None,
            column=meta.get("column"),
            chunk_id=str(chunk_id),
            chunk_index=chunk_idx,
            score=float(match.get("score") or 0.0),
            snippet=snippet,
            extra=extra_from_meta or None,
        )
        citations.append(citation)
        if len(citations) >= limit:
            break
    return citations


def _render_sources_for_prompt(citations: List[Citation]) -> str:
    lines = []

    def _location_label(c: Citation) -> str:
        if c.source_type == "pdf":
            if c.page:
                return f"Page {c.page}"
            return "Document (page unknown)"
        if c.source_type in {"web", "gdrive", "drive", "sharepoint", "onedrive", "notion"}:
            if c.url:
                return f"URL: {c.url}"
            return "Web/Drive document"
        if c.source_type == "email":
            parts = []
            if c.thread_id:
                parts.append(f"thread {c.thread_id}")
            if c.message_id:
                parts.append(f"message {c.message_id}")
            if c.ts:
                parts.append(f"at {c.ts}")
            return "Email " + (" ".join(parts) if parts else "(metadata missing)")
        if c.source_type in {"slack", "teams"}:
            parts = []
            if c.thread_id:
                parts.append(f"thread {c.thread_id}")
            if c.message_id:
                parts.append(f"message {c.message_id}")
            if c.ts:
                parts.append(f"at {c.ts}")
            return f"{c.source_type.title()} " + (" ".join(parts) if parts else "message")
        if c.source_type == "db":
            parts = []
            if c.table:
                parts.append(f"table {c.table}")
            if c.row_id:
                parts.append(f"row {c.row_id}")
            if c.column:
                parts.append(f"column {c.column}")
            return "Database " + (" ".join(parts) if parts else "record")
        return "Document"

    for c in citations:
        title = c.doc_title or c.doc_id
        loc = _location_label(c)
        snippet = c.snippet or ""
        lines.append(f"[{c.id}] {c.source_type.upper()} – \"{title}\"\nLocation: {loc}\nSnippet: \"{snippet}\"")
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
    tag_section = re.findall(r"<citations>(.*?)</citations>", answer, flags=re.IGNORECASE | re.DOTALL)
    for block in tag_section:
        ids.extend(re.findall(r"S(\d+)", block))
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
        "Use ONLY the provided sources as evidence. "
        "Every factual statement must end with at least one citation marker like [S1]. "
        "Never create new citation IDs, titles, URLs, or page numbers—use exactly what is provided. "
        "If the answer is not present in the sources, explicitly say it is not found."
    )
    format_hint = (
        "Respond ONLY with valid JSON using this schema:\n"
        "{\n"
        '  "answer": "<full narrative with [S#] markers and a final <citations> section>",\n'
        '  "bullets": ["optional bullet list"],\n'
        '  "table": {"headers": [], "rows": []},\n'
        '  "citations_used": ["S1","S2"]\n'
        "}\n"
        "Do not invent citation IDs or pages. Omit bullets/table if not needed but keep the keys."
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
        logger.info(
            "index_document doc_id=%s title=%s pages=%s fragments=%s text_len=%s",
            req.document_id,
            (req.doc_title or req.title or "")[:80],
            len(req.pages or []),
            len(req.fragments or []),
            len(req.text or ""),
        )
    except Exception:
        pass
    items: List[Dict[str, Any]] = []
    texts_to_embed: List[str] = []
    metas: List[Dict[str, Any]] = []

    base_title = (req.doc_title or req.title or "").strip() or None
    source_type = _normalize_source_type({"source_type": req.source_type}) or None
    origin_url = (req.origin_url or "").strip() or None
    base_meta = dict(req.metadata or {})
    chunk_counter = 0

    def _append_chunk(text: str, meta_patch: Dict[str, Any], chunk_override: Optional[int] = None):
        nonlocal chunk_counter
        if not text:
            return
        meta = {}
        meta.update({k: v for k, v in base_meta.items() if v is not None})
        meta.update({k: v for k, v in (meta_patch or {}).items() if v is not None})
        meta["document_id"] = req.document_id
        meta["doc_id"] = req.document_id
        if base_title and not meta.get("title"):
            meta["title"] = base_title
        if base_title and not meta.get("doc_title"):
            meta["doc_title"] = base_title
        resolved_type = _normalize_source_type(meta, fallback=source_type) or "document"
        meta["source_type"] = resolved_type
        if origin_url and not meta.get("origin_url"):
            meta["origin_url"] = origin_url
        # Preserve explicit page numbers only; never derive from chunk offsets
        if "page" in meta and meta["page"] is not None:
            try:
                meta["page"] = int(meta["page"])
            except Exception:
                meta["page"] = None
        current_counter = chunk_counter
        chunk_idx = chunk_override if chunk_override is not None else current_counter
        meta["chunk"] = chunk_idx
        chunk_id = meta.get("chunk_id") or f"{req.document_id}:p{meta.get('page') or 0}:c{current_counter}"
        meta["chunk_id"] = chunk_id
        metas.append({k: v for k, v in meta.items() if v is not None})
        texts_to_embed.append(text)
        chunk_counter += 1

    if req.fragments:
        for frag in req.fragments:
            meta_patch = {
                "page": frag.page,
                "url": frag.url,
                "message_id": frag.message_id,
                "thread_id": frag.thread_id,
                "ts": frag.ts,
                "table": frag.table,
                "row_id": frag.row_id,
                "column": frag.column,
                "chunk_id": frag.chunk_id,
                "source_type": frag.source_type,
                "doc_title": frag.doc_title,
                "extra": frag.extra,
            }
            # Respect fragment chunk_id by suffixing split parts to retain location fidelity
            for j, ch in enumerate(chunk_text(frag.text or "", target_chars=1100)):
                derived_chunk_id = frag.chunk_id
                if frag.chunk_id and j > 0:
                    derived_chunk_id = f"{frag.chunk_id}-c{j}"
                _append_chunk(ch, {**meta_patch, **({"chunk_id": derived_chunk_id} if derived_chunk_id else {})}, chunk_override=j if frag.chunk_id else None)
    elif req.pages:
        # Build chunks per page and preserve page number in metadata
        for p in req.pages:
            page_meta = dict(p.meta or {})
            page_meta["page"] = p.page
            for j, ch in enumerate(chunk_text(p.text or "", target_chars=1100)):
                _append_chunk(ch, {**page_meta, "chunk_id": f"{req.document_id}:p{p.page or 0}:c{j}"}, chunk_override=j)
    elif req.text:
        for j, ch in enumerate(chunk_text(req.text or "", target_chars=1200)):
            _append_chunk(ch, {"chunk_id": f"{req.document_id}:c{j}"}, chunk_override=j)
    else:
        return JSONResponse({"ok": False, "error": "no_content", "detail": "Provide text, pages, or fragments"}, status_code=400)

    try:
        embeds = embed_texts(texts_to_embed)
    except Exception as e:
        logger.exception("index_document embed_failed doc_id=%s error=%s", req.document_id, e)
        return JSONResponse({"ok": False, "error": "embed_failed", "detail": str(e)}, status_code=502)

    for i, (text, emb, meta) in enumerate(zip(texts_to_embed, embeds, metas)):
        # ensure unique id across doc
        chunk_key = meta.get("chunk_id") or f"{req.document_id}:{meta.get('chunk') or i}"
        uid = hashlib.sha1(chunk_key.encode("utf-8")).hexdigest()
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
    cite_map = {c.id: _serialize_citation(c) for c in citations}
    ordered_used = [cid for cid in cited_ids if cid in cite_map]
    if not ordered_used:
        ordered_used = [c.id for c in citations[: req.top_k]]
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
