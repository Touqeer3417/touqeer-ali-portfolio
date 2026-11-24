# Portfolio RAG backend

Run these commands from the `backend` directory so Python can import `app` and load
the backend `.env` file:

```powershell
python -m pip install -r requirements.txt
python -m app.ingest
python -m uvicorn app.main:app --reload
```

`python -m app.ingest` incrementally synchronizes Markdown files under `knowledge/`
to the configured Qdrant hybrid collection and writes the matching BM25 corpus to
`.rag-index/bm25-documents.json`. Re-running it updates changed files, indexes new
files, removes deleted file chunks, and leaves unchanged documents alone. Keep the
BM25 snapshot with the deployed instance; it is the local source of truth for the
sparse index and document-version filtering.

The chat endpoint remains `POST /chat` and streams plain text. Dense retrieval uses
the configured Qdrant collection and existing embedding model. Dense and BM25 search
run concurrently and are combined by LangChain's weighted reciprocal rank fusion.
Cross-Encoder reranking is **disabled by default** (`reranker_enabled = False` in
`app/config.py`). To enable it, install the optional dependency with
`python -m pip install -r requirements-reranker.txt` and set `RERANKER_ENABLED=true`
in `.env`; it uses the configured `cross-encoder/ms-marco-MiniLM-L-6-v2` model. Measured
note: the first request after a cold start paid about 20 s to load the model. The model loads lazily once per
process; if loading or scoring fails, hybrid retrieval keeps its original result order.

### Chunking settings (`app/config.py`, override via `.env`)

| Setting | Default | Purpose |
|---|---|---|
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | 800 / 120 | Recursive splitter size and overlap |
| `MIN_CHUNK_CHARS` | 100 | Chunks shorter than this (title-only or overlap leftovers) are merged into a neighbour or dropped |
| `CHUNK_CONTEXT_PREFIX` | true | Stores `[Source: file | Project: ... | Section: ...]` at the top of each chunk so continuation chunks match topic words |

Each chunk records the chunking settings it was built with. `python -m app.ingest`
compares them with the current settings and re-indexes any file built with different
ones, even if the file itself is unchanged, so the index cannot silently drift from
the configuration. After changing any of these settings, run `python -m app.ingest`
before evaluating.

## Response cache

Repeated **first-turn** questions (the widget's starter prompts, the handful of
things every visitor asks) are served from `app/response_cache.py`, which skips
retrieval and generation entirely, so a hit spends no OpenAI tokens.

| Setting | Default | Purpose |
|---|---|---|
| `RESPONSE_CACHE_SIZE` | 256 | Bounded LRU of answers; `0` disables the cache |
| `RESPONSE_CACHE_TTL_SECONDS` | 1800 | How long an answer stays servable; `0` disables the cache |

- **Scope:** only a conversation's first turn is cached. Once there is history the
  answer depends on conversation state (the project scope carried over by
  `retrieval.document_awareness`, and the history in the prompt), so it is never
  reused. Enforced by `app.rag.cacheable_question`.
- **Keys:** `(chat model, knowledge-base fingerprint, normalized question)`.
  Normalization reuses `embedding_cache.normalize_query`, so case, spacing and
  trailing punctuation share one entry while different words never do.
- **Invalidation:** the fingerprint is the `stat()` of `.rag-index/bm25-documents.json`,
  which `python -m app.ingest` republishes for every generation. Re-indexing therefore
  retires every cached answer immediately, independently of the TTL. The cache is
  per process, so code and settings changes are cleared by the deploy that restarts it.
- **Never cached:** error fallbacks, the no-context reply, partially streamed or
  cancelled answers, and empty generations.
- **Metrics:** `GET /cache/stats` (same shared secret as `/chat`) returns hits,
  misses, hit rate, evictions and expirations for the worker that answers. A hit is
  also flagged per request as `response_cache_hit` in `GET /latency/{request_id}`,
  and logged as `rag_stage stage=response_cache_hit`.
- **Evaluation:** `evaluation/pipeline_adapter.py` wraps each sample in
  `bypass_response_cache()`, so RAGAS scores and `app.latency_benchmark` always
  measure a real retrieval and generation run even when a dataset repeats a question.

Run backend unit tests from this directory:

```powershell
python -m unittest discover -s tests -v
```

## Streaming

`POST /chat` streams `text/plain` end to end: the LangChain chain's `astream` output
is yielded token by token by `app.rag.stream_answer`, FastAPI sends it with
`Cache-Control: no-cache, no-transform` and `X-Accel-Buffering: no`, the Next.js route
(`src/app/api/chat/route.ts`) passes the body through untouched, and the chat widget
renders each chunk as it arrives.

- **Cancellation:** the widget's Stop button (or closing/leaving the page) aborts the
  browser request; the Next route aborts the upstream request; Starlette then cancels
  the response task so `stream_answer`'s `finally` blocks run (latency record, logging).
  The cancellation is logged as `chat stream cancelled by client`.
- **Errors:** a failure after some tokens were streamed keeps the partial answer and
  appends the apology on a new paragraph. Failures before the first byte return
  HTTP 401/429/502 and the widget shows a friendly message.

`tests/test_streaming.py` covers progressive delivery, cleanup on early close and
cancellation, mid-stream failure, response headers, and (over real loopback HTTP)
client-disconnect cancellation.
