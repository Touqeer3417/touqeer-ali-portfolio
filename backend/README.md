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
