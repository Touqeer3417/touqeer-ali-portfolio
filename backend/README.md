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
