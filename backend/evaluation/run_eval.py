"""End-to-end portfolio RAG evaluation using the deployed/local FastAPI endpoint."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
CASES_PATH = HERE / "cases.json"
RESULTS_DIR = HERE / "results"

ABSTENTION_MARKERS = (
    "do not have that detail",
    "don't have that detail",
    "could not find",
    "not available in",
    "not mentioned",
    "not documented",
    "insufficient information",
    "knowledge base does not",
    "maujood nahi",
    "maloom nahi",
    "mention nahi",
)


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(p * len(ordered)) - 1)]


def contains_any(text: str, alternatives: list[str]) -> bool:
    lowered = text.casefold()
    return any(term.casefold() in lowered for term in alternatives)


def call_chat(api_base: str, secret: str, messages: list[dict], timeout: float) -> tuple[str, float]:
    payload = json.dumps({"messages": messages}).encode("utf-8")
    request = Request(
        api_base.rstrip("/") + "/chat",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": secret,
        },
        method="POST",
    )
    started = time.perf_counter()
    with urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8", errors="replace")
    return body, (time.perf_counter() - started) * 1000


def retrieval_probe(messages: list[dict]) -> tuple[list[str], float]:
    # Optional: an additional retrieval call. It is intentionally not included
    # in normal endpoint latency measurements because it duplicates retrieval.
    from app.rag import retrieval_query, retrieve_documents

    query = retrieval_query(messages)
    started = time.perf_counter()
    documents = retrieve_documents(query)
    elapsed = (time.perf_counter() - started) * 1000
    sources = []
    for document in documents:
        source = document.metadata.get("source")
        if isinstance(source, str) and source not in sources:
            sources.append(source)
    return sources, elapsed


def evaluate_case(case: dict, answer: str) -> dict:
    expected_groups = case.get("expected_any", [])
    matched_groups = [
        contains_any(answer, alternatives)
        for alternatives in expected_groups
    ]
    fact_score = (
        sum(matched_groups) / len(matched_groups)
        if matched_groups else None
    )
    abstained = contains_any(answer, list(ABSTENTION_MARKERS))
    forbidden = any(
        contains_any(answer, alternatives)
        for alternatives in case.get("forbidden_any", [])
    )
    must_abstain = case.get("must_abstain", False)
    must_mention_unavailable = case.get("must_mention_unavailable", False)

    passed = all(matched_groups) and not forbidden
    if must_abstain:
        passed = abstained and not forbidden
    if must_mention_unavailable:
        passed = passed and abstained

    return {
        "passed": bool(passed),
        "fact_score": fact_score,
        "matched_fact_groups": sum(matched_groups),
        "expected_fact_groups": len(matched_groups),
        "abstained": abstained,
        "forbidden_claim_detected": forbidden,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-base", default=os.getenv("RAG_API_BASE_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--secret", default=os.getenv("SHARED_SECRET"))
    parser.add_argument("--limit", type=int, default=0, help="Run only the first N cases (0 = all).")
    parser.add_argument("--pause-seconds", type=float, default=6.2)
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument("--retrieval-probe", action="store_true")
    args = parser.parse_args()

    if not args.secret:
        parser.error("Set SHARED_SECRET or pass --secret. Do not commit this value.")

    suite = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    cases = suite["cases"]
    if args.limit > 0:
        cases = cases[:args.limit]

    results = []
    for index, case in enumerate(cases):
        messages = case["messages"]
        row = {
            "id": case["id"],
            "category": case["category"],
            "expected_sources": case.get("expected_sources", []),
        }

        if args.retrieval_probe:
            try:
                sources, retrieval_ms = retrieval_probe(messages)
                row["retrieved_sources"] = sources
                row["retrieval_probe_ms"] = round(retrieval_ms, 1)
                expected_sources = row["expected_sources"]
                row["source_relevant"] = (
                    all(source in sources for source in expected_sources)
                    if expected_sources else len(sources) == 0
                )
            except Exception as exc:  # report probe failures without losing API test
                row["retrieval_probe_error"] = type(exc).__name__

        try:
            answer, latency_ms = call_chat(
                args.api_base, args.secret, messages, args.timeout
            )
            checks = evaluate_case(case, answer)
            row.update(checks)
            row["latency_ms"] = round(latency_ms, 1)
            row["answer"] = answer
        except HTTPError as exc:
            row.update({"passed": False, "error": f"HTTP {exc.code}"})
        except (URLError, TimeoutError, OSError) as exc:
            row.update({"passed": False, "error": f"request_error: {type(exc).__name__}"})

        results.append(row)
        status = "PASS" if row.get("passed") else "FAIL"
        latency = row.get("latency_ms")
        print(f"{status:4} {case['id']} {case['category']} latency_ms={latency if latency is not None else 'n/a'}")

        if index < len(cases) - 1 and args.pause_seconds > 0:
            time.sleep(args.pause_seconds)

    latencies = [row["latency_ms"] for row in results if "latency_ms" in row]
    evaluated = [row for row in results if "passed" in row]
    abstention_cases = [
        row for row, case in zip(results, cases) if case.get("must_abstain")
    ]
    answerable = [
        row for row, case in zip(results, cases)
        if case.get("expected_any") and not case.get("must_abstain")
    ]
    probe_rows = [row for row in results if "source_relevant" in row]

    summary = {
        "total_cases": len(cases),
        "completed_cases": len(evaluated),
        "passed": sum(row["passed"] for row in evaluated),
        "failed": sum(not row["passed"] for row in evaluated),
        "average_latency_ms": round(statistics.mean(latencies), 1) if latencies else None,
        "p50_latency_ms": round(percentile(latencies, 0.50), 1) if latencies else None,
        "p95_latency_ms": round(percentile(latencies, 0.95), 1) if latencies else None,
        "answerable_fact_match_rate": round(
            statistics.mean(row["fact_score"] for row in answerable if row["fact_score"] is not None), 3
        ) if any(row["fact_score"] is not None for row in answerable) else None,
        "fallback_accuracy": round(
            statistics.mean(row["abstained"] for row in abstention_cases), 3
        ) if abstention_cases else None,
        "retrieval_source_relevance_rate": round(
            statistics.mean(row["source_relevant"] for row in probe_rows), 3
        ) if probe_rows else None,
        "retrieval_probe_average_ms": round(
            statistics.mean(row["retrieval_probe_ms"] for row in probe_rows if "retrieval_probe_ms" in row), 1
        ) if any("retrieval_probe_ms" in row for row in probe_rows) else None,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = RESULTS_DIR / f"eval_{stamp}.json"
    output_path.write_text(
        json.dumps({"summary": summary, "results": results}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    csv_path = output_path.with_suffix(".csv")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        fields = ["id", "category", "passed", "latency_ms", "fact_score", "abstained", "forbidden_claim_detected", "error", "answer"]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    print("\nSUMMARY")
    print(json.dumps(summary, indent=2))
    print(f"JSON report: {output_path}")
    print(f"CSV report:  {csv_path}")
    return 0 if summary["failed"] == 0 and summary["completed_cases"] == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
