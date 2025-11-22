# Universal Citation Model

DocuIQ now uses one canonical schema across ingestion, retrieval, prompting,
backend responses, and the Vue UI. Every citation object is shaped as:

| Field | Description |
| --- | --- |
| `id` / `citation_id` | Stable ID like `S1`, assigned per answer. |
| `source_type` | `pdf`, `web`, `email`, `slack`, `teams`, `gdrive`, `db`, … |
| `doc_id` | Internal document identifier. |
| `doc_title` | Human-readable title (filename, page title, subject, etc.). |
| `snippet` | Direct substring from the original text used as evidence. |
| `score` | Retrieval score from the vector search. |
| `page` | 1-based page number (present only when provided by ingestion). |
| `url` | Deep link to the original source or viewer. |
| `message_id` / `thread_id` / `ts` | Email/chat metadata. |
| `table` / `row_id` / `column` | Database location metadata. |
| `chunk_id` / `chunk_index` | Chunk tracking for debugging. |
| `extra` | Provider-specific metadata (channel, sender, workspace, etc.). |

## Ingestion

- `backend/ingest/tasks.py` forwards `source_type`, `origin_url`, and captured
  connector metadata (`message_id`, `thread_id`, `table`, etc.) via the
  `metadata` field to `ai_engine/index_document`.
- PDFs store real page numbers straight from extraction; no downstream guesses.
- Web captures include `source_url` and parsed `<title>` as `doc_title`.
- Email/Slack/Teams/GDrive/DB connectors can pass fragments or `metadata`
  directly so every chunk is tagged before embedding.
- `ai_engine/index_document` writes `doc_id`, `doc_title`, `source_type`, page,
  and all location metadata onto each chunk.

## Retrieval & Prompting

- `ai_engine/_build_citations` converts vector matches into the canonical model,
  keeping only metadata provided at ingestion time.
- Prompt context lists sources as:

  ```
  [S1] PDF – "Climate Report 2023"
  Location: Page 48
  Snippet: "Scope 1 emissions declined 10% year over year..."
  ```

- The LLM is instructed to cite only provided IDs, avoid inventing titles/pages,
  and return JSON with `citations_used`. `<citations> S1 S3 </citations>` blocks
  are also parsed for redundancy.

## Backend Responses

- The AI engine returns `answer`, `citations`, `all_citations` (debug), and
  `inline_refs` keyed by `S#`. Django chat history stores these payloads
  unchanged for replay.

## Frontend Rendering

- `frontend/src/components/citations/CitationChip.vue` renders every citation
  with a source-type icon, normalized label, and a tooltip snippet. Clicks open
  the supplied URL or the internal document viewer.
- `StructuredBlocks.vue` and `NewAnalysisChat.vue` consume the canonical fields
  (`id`, `sourceType`, `docTitle`, `page`, `snippet`, `url`, etc.) and
  propagate the `href` to the router or external window.
