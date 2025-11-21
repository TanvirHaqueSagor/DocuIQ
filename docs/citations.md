# DocuIQ Citation Pipeline

DocuIQ now uses a single canonical citation schema through ingestion, retrieval,
API responses and the frontend UI. Every citation object contains:

| Field | Description |
| --- | --- |
| `citation_id` | Stable ID such as `S1`, assigned per answer. |
| `doc_id` | Internal `IngestFile` identifier for the document. |
| `doc_title` | Human-friendly title/filename used in pills. |
| `source_type` | Origin of the content (`pdf`, `web`, etc.). |
| `page` | 1-based page number captured at ingestion time. |
| `chunk_id` / `chunk_index` | Exact chunk reference for logging/debugging. |
| `score` | Cosine similarity from the vector search. |
| `snippet` | 1–3 sentences of the chunk text rendered in the UI tooltip. |
| `url` | Link to open the PDF viewer at the cited page. |

## Ingestion

`backend/ingest/tasks.py` passes `source_type` and `origin_url` to the AI
engine, and `ai_engine/index_document` stores `doc_id`, `page`, `chunk_id` and
origin metadata for every chunk. Page numbers are persisted directly from the
PDF extraction; there are no heuristics later in the pipeline.

## Retrieval & LLM Prompting

The AI engine (`ai_engine/main.py`) converts top search matches into structured
citations before calling the LLM. The model receives enumerated snippets:

```
[S1] Document: Climate Report 2023
Page: 48 | Type: pdf
Snippet: Scope 1 emissions declined 10% year over year...
```

The prompt instructs the model to reference only these IDs and to return JSON:

```
{
  "answer": "Scope 1 emissions fell 10% [S1].",
  "citations_used": ["S1"]
}
```

If JSON parsing fails we fall back to scanning for `[S#]` markers. The final API
response always includes `citations`, `all_citations` (debug), and
`inline_refs`.

## Backend APIs

Chat history (`backend/chats/views.py`) stores the canonical citation JSON
directly, so Document Detail references can match `doc_id` and `url` reliably.
Any new API responses should forward the `citations` and `inline_refs` payloads
from the AI engine verbatim.

## Frontend Rendering

`frontend/src/components/chat/NewAnalysisChat.vue` consumes the canonical
`citations` array and feeds it into `StructuredBlocks.vue`. Citation pills show
“Page N — Title” with the snippet underneath, and clicking a pill opens the PDF
viewer (`/documents/:id?p=page`). The same structure is stored in chat history
so future UIs can reuse `<StructuredBlocks>` directly.
