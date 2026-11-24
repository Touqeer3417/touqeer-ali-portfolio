# Portfolio RAG evaluation

This folder evaluates the existing portfolio assistant. It does not add endpoints,
change retrieval, or replace the production prompt/generation flow.

## Files

- `config.py` — dataset/report paths and metric names.
- `dataset.py` — validates question/reference records.
- `pipeline_adapter.py` — calls the existing `app.rag.stream_answer` and captures
  the documents returned by its real retriever.
- `metrics.py` — creates RAGAS 0.4 collection metrics and wraps the application's
  configured LLM and embedding models.
- `evaluator.py` — runs each sample, scores it, and writes a report.
- `report.py` — summarizes valid scores and saves timestamped JSON reports.
- `datasets/evaluation_dataset.json` — manually verified portfolio questions and
  references based on `backend/knowledge/*.md`.
- `datasets/evaluation_dataset_extended.json` — the 12 original cases (unchanged, first)
  plus out-of-scope, prompt-injection, multi-project, list-completeness and Roman Urdu
  cases, all grounded in `backend/knowledge/*.md`. Run it with
  `python -m evaluation.evaluator --warmup --dataset evaluation\datasets\evaluation_dataset_extended.json`.
  Scores from different datasets are not directly comparable; compare like with like.
- `tests/test_evaluation.py` — offline tests using mocks; no API calls.
- `reports/` — generated reports are written here when the evaluator runs.

## Dependencies and run commands

Run from the project root in PowerShell. The evaluation uses a separate ignored
virtual environment so it does not install RAGAS into the assistant's `portfolio_rag`
environment. Its evaluation requirements pin the verified production versions of
`langchain-core`, `langchain-classic`, `langchain-qdrant`, `langchain-openai`,
`qdrant-client`, and `rank-bm25`. The only intentional retrieval dependency mismatch
is `langchain-community`: production has 0.4.2 while the RAGAS environment requires
0.3.31 for RAGAS 0.4.3 compatibility. Production dependencies are not changed.
Evaluation requirements also install `requirements-reranker.txt`, so the shared
application configuration enables the same Cross-Encoder in both environments.

```powershell
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m ensurepip --upgrade
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip install -r evaluation\requirements-eval.txt
.venv\Scripts\python.exe -m unittest discover -s evaluation\tests -v
.venv\Scripts\python.exe -m evaluation.evaluator
```

The evaluator reads the existing `backend/.env` configuration (OpenAI and Qdrant)
and makes real retrieval, answer-generation, and RAGAS judge calls. These calls may
incur provider usage costs. It reads the existing Qdrant collection; it does not run
ingestion or modify either index. Run it when provider credentials and the local
BM25 snapshot are available.

## Dataset format

Each record has a unique `id`, `user_input`, and, when available, a ground-truth
`reference` written from the Knowledge Base. Add references only after checking
them against source Markdown. A missing or blank reference does not stop a run:
Answer Relevancy and Faithfulness are still calculated, while Answer Correctness,
Context Recall, and Context Precision remain null and are explicitly marked as not
evaluated. The evaluator never derives references from model responses.

For every case, the adapter adds:

- `retrieved_contexts` — page contents of chunks returned by the production hybrid
  retriever.
- `response` — concatenated tokens from the existing streaming generation function.

No separate retriever, embedding model, vector store, or answer generator is created.
The adapter observes the existing retrieval call within a scoped patch in this
standalone evaluation process. The production application source and API are unchanged.

## Metrics

All five metrics use the RAGAS 0.4 collection API:

- **Answer Correctness** compares the response with the verified reference.
- **Answer Relevancy** checks whether the response addresses the question.
- **Faithfulness** checks whether answer claims are supported by retrieved context.
- **Context Recall** checks whether the retrieved context supports reference claims.
- **Context Precision** checks the relevance and ranking of retrieved context against
  the reference.

The evaluator uses the existing configured chat model and its async OpenAI client.
RAGAS 0.4 collection metrics require RAGAS-native OpenAI embeddings, so the module
creates an evaluation client using the existing embedding model and API key. It does
not use those embeddings for retrieval. Missing contexts and pipeline failures are marked as
incomplete/failed and are not assigned invented scores. Individual metric errors are
recorded; failed metric scores remain `null` and are excluded from aggregate means.

Each run writes a timestamped JSON file under `evaluation/reports/` with per-question
inputs, contexts, response, metric scores/errors, aggregate means, and failed or
incomplete cases. RAGAS uses LLM judgments, so scores can vary slightly between runs.

## Dependency parity

Production (the `portfolio_rag` environment) currently uses LangChain Core 1.7.6,
Community 0.4.2, Classic 1.0.8, Qdrant integration 1.1.0, Qdrant client 1.20.0,
BM25 0.2.2, and OpenAI integration 1.7.4. The evaluation environment pins the same
versions except Community 0.3.31, due to the RAGAS 0.4.3 compatibility constraint.
Dense Qdrant and RRF implementations therefore run against matched Core/Classic/
Qdrant packages; the `BM25Retriever` comes from the version-mismatched Community
package. Live retrieval parity must be rechecked in both environments after any
dependency or index change. If the external Qdrant service is unreachable, parity
cannot be claimed based on offline unit tests alone.

In the verification run for this change, the pre-existing evaluation `.venv` still
had Core 1.8.0. Installing the newly pinned Core 1.7.6 was blocked by package-index
network access, so the fresh RAGAS run used Core 1.8.0. The three-query retrieval
comparison returned identical ordered chunk IDs and content hashes in both current
environments, but the version pin needs to be installed and the run repeated for
full dependency parity.
