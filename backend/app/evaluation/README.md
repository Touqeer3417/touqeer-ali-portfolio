# Offline RAGAS evaluation

This package evaluates the existing portfolio RAG pipeline without changing visitor chat behavior. It calls the same hybrid Qdrant retriever, prompt, and configured chat model used by `app.rag.stream_answer`; each evaluation question is retrieved once and generated once.

## Install

From `backend/` with the project's supported Python environment:

```bash
pip install -r evaluation-requirements.txt
```

The RAGAS dependency is intentionally kept in a separate requirements file so the production FastAPI image does not need the evaluator dependencies. The normal `requirements.txt` is unchanged.

## Configure

Use the existing backend `.env` values: `OPENAI_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`, and the existing model settings if overridden. No additional secrets or environment variables are required. The configured chat model is used for generation and RAGAS judging; the configured embedding model is used for Answer Relevancy.

## Run

From `backend/`:

```bash
python -m app.evaluation.runner
```

The runner loads the curated, source-checked cases in `app/evaluation/dataset.json`, captures the original ordered retrieval contexts and the actual generated answer, scores the four metrics asynchronously, and writes a timestamped JSON report under `evaluation/reports/`. Reports are ignored by Git because they can contain retrieved portfolio context and model outputs.

## Metrics

- **Context Recall**: decomposes the reference answer into claims and estimates the proportion supported by the retrieved contexts.
- **Context Precision**: judges each retrieved context against the reference answer and rewards relevant contexts appearing earlier in the unchanged Qdrant RRF ranking.
- **Answer Relevancy**: generates likely questions from the response and compares their embeddings with the original user question.
- **Faithfulness**: decomposes the generated answer into claims and checks whether each claim is supported by the exact contexts supplied to generation.

All scores are retained as returned by RAGAS. A failed metric is recorded as an error and is never replaced with zero. Answer Relevancy uses cosine similarity and is not forcibly clamped to a 0–1 range.

## Reports and failures

Each report includes dataset/sample counts, evaluator and RAGAS versions, UTC timestamp, aggregate scores, per-question references, retrieved contexts, generated answers, individual metric scores and explicit errors. A metric average is calculated only from successful numeric scores for that metric. Partial sample failures remain visible in the report.

The evaluator uses bounded sample concurrency and per-operation timeouts. It is an offline developer command and is never invoked by the FastAPI `/chat` endpoint.

## Unit tests

From `backend/`, run the mock-based test suite with:

```bash
python -m unittest discover -s tests -v
```

The RAGAS import/constructor tests are skipped when the separate evaluation requirements have not been installed. No live API calls are made by the unit tests.
