# Portfolio RAG API

This folder contains the FastAPI service used by the portfolio chat proxy.

## Request flow

Browser chat widget -> Next.js `/api/chat` proxy -> FastAPI `/chat` -> Qdrant hybrid retrieval (dense embeddings + BM25 + reciprocal-rank fusion) -> OpenAI chat model -> streamed text response.

The Next.js server sends `RAG_API_SECRET` as `x-api-key`. Do not place the shared secret in a `NEXT_PUBLIC_*` variable or browser code.

## Local setup (PowerShell)

Run these commands from the `backend` directory:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Edit `.env` and set `OPENAI_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`, and `SHARED_SECRET`. The shared secret must be at least 24 characters and must match the Next.js/Vercel `RAG_API_SECRET`.

Index the portfolio knowledge files, then start the API:

```powershell
python -m app.ingest
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Health check: `http://127.0.0.1:8000/health`

## Tests

In another PowerShell window, activate the same virtual environment, change to `backend`, and run:

```powershell
python -m pytest tests -q
```

The tests mock retrieval/model calls where appropriate; they do not need live OpenAI or Qdrant requests.

## End-to-end evaluation

With the API running and `SHARED_SECRET` set in the current PowerShell session:

```powershell
$env:RAG_API_BASE_URL = "http://127.0.0.1:8000"
$env:SHARED_SECRET = "your-same-backend-shared-secret"
python -m evaluation.run_eval
```

The evaluation sends 43 portfolio-grounded cases. It waits 6.2 seconds between calls by default to stay below the API's 10-per-minute rate limit. Results are written under `evaluation/results/`. Use `--limit 5 --pause-seconds 0` for a short smoke test. Automated answer checks are exact phrase heuristics, not a substitute for reviewing factual claims manually.

To separately inspect whether expected knowledge files are retrieved, use `--retrieval-probe`. This performs an additional embedding + Qdrant retrieval for each case, so do not use that option when measuring normal end-to-end latency.

## Deployment

Render root directory: `backend`

Build command: `pip install -r requirements.txt`

Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Set the environment variables shown in `.env.example` in Render. In Vercel, set `RAG_API_URL` (without a trailing slash) and `RAG_API_SECRET`, then redeploy.
