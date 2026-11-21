# Portfolio AI Assistant — Engineering Audit Report
Date: 2026-11-21 · Scope: `D:\touqeer-ali-portfolio` (backend/, evaluation/, Next.js chat integration)

**How to read this report.** "Verified" = read in code or produced by running code in a scratch copy. "Measured" = taken from your saved RAGAS/latency reports. "Estimate" = reasoning only. I had no shell on your PC, so I could **not** run the live pipeline, a fresh benchmark, a RAGAS run, `git status`, or a frontend build. Phase 5 benchmark steps are therefore *not done* (see section 7).

## 1. Architecture
Next.js `ChatWidget` → `/api/chat` proxy (adds secret + client IP) → FastAPI `POST /chat` (secret check, slowapi 10/min & 80/day) → `rag.stream_answer`.
Pipeline: query = last 2 user turns → project resolver → dense (Qdrant) ‖ BM25 → weighted RRF → optional cross-encoder → top 5 chunks → prompt → `gpt-4o-mini` (`max_tokens=350`, temp 0.3) streamed as plain text. Knowledge base: 5 Markdown files, ~17 KB.

## 2. Measured baseline (from your reports; 12 questions, run from your PC)
| Run | Reranker | Avg total | p50 | Avg TTFT | Avg retrieval | Avg embedding | Avg LLM |
|---|---|---|---|---|---|---|---|
| 14 Nov latency report | on | 6,553 ms | 3,656 | 4,992 | 3,722 | 462 | 2,830 |
| 21 Nov 06:58 | off | 4,814 | 3,739 | 3,914 | 2,995 | 763 | 1,817 |
| 21 Nov 07:56 | off | 2,293 | 2,024 | 1,422 | 757 | 357 | 1,535 |

p95 is not reliable (n=12; the report says so). Run-to-run variance is large (network + code changes between runs), so single runs cannot prove an improvement.

| RAGAS (means) | Reranker on (3 runs, 14 Nov) | Reranker off (3 runs, 21 Nov) |
|---|---|---|
| answer_correctness | 0.76–0.83 | 0.78–0.82 |
| answer_relevancy | ~0.77 | ~0.766 |
| faithfulness | 0.985 | 0.97–1.00 |
| context_recall | 1.00 | 1.00 |
| context_precision | 0.79–0.86 | 0.71 |
Same dataset and knowledge files, but other code also changed between the two groups.

## 3. Findings
### F1 — Project filter sticks to an earlier turn (CRITICAL for answer quality) — *reproduced offline*
- **Evidence:** `rag.py:retrieval_query` joins the last 2 user turns; `hybrid.py:_aget_relevant_documents` runs `resolve_project` on that joined text and filters BOTH dense (`dense.py` `metadata.project_id` filter) and BM25 (`sparse.py` project subset). Repro (`repro_project_filter_followup.py`): after "Tell me about … Corrective RAG project", the follow-up "How can I contact him for a project?" gives BM25 results `['projects.md','projects.md']`; unscoped it gives `['contact.md', …]`.
- **Root cause:** project detection uses old-turn text, and the filter excludes every chunk without a `project_id` (contact, about, services, skills).
- **Impact:** after any project question, follow-ups on contact/services/skills can be answered "not specified" even though the data exists. The 12-question eval is single-turn, so it cannot see this. The dense side was verified by code reading, not executed.
- **Fix:** resolve the project from the latest user message only (or fall back to unscoped search when the filter result lacks the question's topic); add a multi-turn test.
- **Expected improvement:** correctness for follow-ups (estimate; not measurable with current dataset). **Trade-off:** a vague follow-up like "what stack does it use?" loses the project scope; handle with a short query rewrite or keep the previous project only when the new message has no topic words.

### F2 — Errors are returned as normal answers (HIGH, reliability)
`rag.py` lines ~305–311 yield an apology string inside an HTTP 200 stream, appended after any partial answer. The client cannot tell failure from content, so it cannot retry or log. **Fix:** emit an explicit end-of-stream error marker or trailer the widget understands. **Trade-off:** small API-contract change (widget + proxy).

### F3 — Reranker cold start is never warmed (HIGH if enabled)
`warmup.py` warms BM25, embeddings, Qdrant and the LLM but not `_cross_encoder()`. Measured: the first request with the reranker on took 35.9 s (≈19.9 s reranking). It is off by default now, so this only bites if you re-enable it. Also: with it off, precision measured 0.71 vs ~0.8. **Fix:** if `reranker_enabled`, load the model in `warm_up`; decide on/off using the K-sweep you already scripted (no K=4/3 reports exist yet). **Trade-off:** torch dependency and memory on small hosts.

### F4 — Raw Markdown shown in the chat (MEDIUM, UX)
`ChatWidget.tsx` renders `whitespace-pre-wrap` text, but the model returns `**bold**`, bullet lists and links (see the corrective_rag response in the 21 Nov report). **Fix options:** (a) cheapest: tell the prompt "plain text, no Markdown" (changes generation → re-run RAGAS); (b) render Markdown with a sanitised renderer (new dependency).

### F5 — Whole knowledge base fits in one prompt (MEDIUM, architecture decision)
~17 KB ≈ 4–5K tokens. A "stuff everything + OpenAI prompt caching" baseline would remove embedding + Qdrant + BM25 (≈0.75 s of 2.3 s in the best run — estimate) and removes retrieval misses like F1. **Trade-off:** it stops demonstrating RAG (the portfolio's selling point) and does not scale if the KB grows. **Recommendation:** keep RAG, but add a long-context baseline to the eval so the choice is data-driven.

### F6 — Evaluation & tests (MEDIUM)
- Verified: `test_ensemble_runs_dense_and_bm25_concurrently_and_fuses` failed on a clean checkout (needed the gitignored `.rag-index` and live Qdrant). **Fixed** (section 5).
- 12 single-turn English questions; none for Roman Urdu, off-topic, prompt injection or multi-turn, though the system prompt promises them.
- Judge model = generator model (`gpt-4o-mini`) → self-preference bias.
- Abstention cases (`professional_experience_years`, `service_pricing`) score relevancy 0 and recall 0; this is probably RAGAS penalising "not specified" answers, not a bug — unconfirmed.
- No CI workflow found; no p95-grade sample size.

### F7 — Backend hardening (LOW–MEDIUM)
Rate limiter and latency records are in-process (reset on restart, not shared across workers); `x-client-ip` is trusted from any caller who holds the secret; proxy had no timeout (fixed); `RAG_API_URL` missing would call `undefined/chat` (fixed). BM25 snapshot is gitignored while the README says to ship it, so a fresh deploy rebuilds from Qdrant on first use.

### F8 — Micro-inefficiencies (LOW, unmeasured)
Per-request rebuild of `QdrantVectorStore`/ensemble, an O(corpus) dict build in `_normalize_documents`, BM25 scored twice (`_with_scores`). With ~30 chunks this is negligible; not worth touching without a profile.

### F9 — Hygiene (LOW)
Duplicate chat code in `portfolio-rag-chatbot/frontend/`; empty `index.txt` files; no Dockerfile/`render.yaml` in the repo (deployment not verifiable); many evaluation report JSONs (≈250 KB each) are not gitignored (git state unverified).

## 4. Roadmap
- **P0:** F1 (project scope), F2 (error signalling). Both need a multi-turn eval case added first.
- **P1:** F4 (Markdown), F3 (decide reranker via K-sweep; warm it if on), expand eval set (Roman Urdu, off-topic, injection, multi-turn, ≥20 questions so p95 means something), use a different judge model.
- **P2:** CI running `unittest` offline; shared rate-limit store if you scale past one worker; remove duplicate frontend copy.
- **P3:** long-context baseline experiment (F5); micro-optimisations only if profiling justifies.

## 5. Changes implemented (3 files, minimal diffs, original CRLF/LF preserved)
1. `backend/tests/test_hybrid_rag.py` — the ensemble test no longer touches the BM25 snapshot or Qdrant. Verified: **48/48 backend tests pass** in a clean scratch copy (before: 47/48).
2. `backend/README.md` — reranker is documented as disabled by default (matches `config.py`) and notes the ~20 s cold load.
3. `src/app/api/chat/route.ts` — `AbortSignal.timeout(55_000)` on the upstream call and a clear 500 when `RAG_API_URL` is unset. **Not compiled or run** (no node_modules here); please run `npm run build`.

## 6. Not implemented, and why
F1, F2, F3, F4: they change retrieval, generation or the API contract, and I cannot run RAGAS or the live pipeline from here to prove they do not reduce quality. Your rule "don't optimise blindly" applies. F5/F6/F7/F9: need your decisions or a bigger dataset.

## 7. Not verified
Live latency in production; before/after benchmarks; RAGAS results for any change; `git status`/uncommitted work; `.env` values (deliberately not read); frontend build; the dense-side behaviour of F1 beyond code reading; whether RAGAS abstention scoring is a metric artefact.

## 8. Next steps (PowerShell, from `backend`)
```powershell
python -m unittest discover -s tests -v
python repro_project_filter_followup.py
.\run_topk_sweep.ps1 -Limits 5,4,3      # needed to settle F3
```
Then implement F1 + a multi-turn eval case, re-run `python -m evaluation.evaluator --warmup`, and compare with `compare_reports.py`.
