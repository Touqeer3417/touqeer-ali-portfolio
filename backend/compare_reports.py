"""Compare the newest RAGAS reports side by side (read-only).

    python compare_reports.py --last 3

Each report is labelled by the largest context size it used (``final_top_k``
recorded per sample, i.e. the effective RRF_LIMIT), so a sweep over RRF_LIMIT reads straight off the table.
Gate (relaxed): context_recall must stay 1.00 and faithfulness must be >= 0.95.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

REPORTS = Path(__file__).resolve().parent / "evaluation" / "reports"
METRICS = ["answer_correctness", "answer_relevancy", "faithfulness", "context_recall", "context_precision"]
FAITHFULNESS_MIN = 0.95


def _summarize(path: Path) -> dict:
    report = json.loads(path.read_text(encoding="utf-8"))
    samples = report["samples"]
    # final_top_k is len(selected) per question: project-specific questions have fewer
    # candidates than RRF_LIMIT, so the configured limit shows up as the maximum.
    ks = [(s.get("retrieval_trace") or {}).get("final_top_k") for s in samples]
    ks = [k for k in ks if k is not None]
    latency = (report.get("latency_summary") or {}).get("all") or {}

    def stat(stage: str, key: str = "average") -> float | None:
        return (latency.get(stage) or {}).get(key)

    return {
        "file": path.name,
        "k": str(max(ks)) if ks else "?",
        "chunks": statistics.mean(len(s.get("retrieved_contexts") or []) for s in samples),
        "metrics": {m: (report["metric_summary"].get(m) or {}).get("mean") for m in METRICS},
        "failed": len(report.get("failed_or_incomplete_samples") or []),
        "total": stat("total_ms"),
        "ttft": stat("ttft_ms"),
        "llm_ttft": stat("llm_ttft_ms"),
        "llm": stat("llm_ms"),
        "retrieval": stat("retrieval_ms"),
    }


def _fmt(value, scale: float = 1.0, digits: int = 3) -> str:
    return "  n/a" if value is None else f"{value / scale:.{digits}f}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--last", type=int, default=3, help="how many newest reports to compare")
    args = parser.parse_args()

    files = sorted(REPORTS.glob("ragas_*.json"))[-args.last :]
    if not files:
        raise SystemExit(f"No ragas_*.json reports in {REPORTS}")
    rows = [_summarize(f) for f in files]

    print(f"{'report':<34}{'K':>4}{'chunks':>8}  " + "  ".join(m.replace('answer_', 'a_').replace('context_', 'c_')[:9].rjust(9) for m in METRICS))
    for r in rows:
        print(f"{r['file'][:33]:<34}{r['k']:>4}{r['chunks']:>8.1f}  " + "  ".join(_fmt(r['metrics'][m]).rjust(9) for m in METRICS))

    print("\nlatency, average over all samples (seconds)")
    print(f"{'K':>4}  {'retrieval':>9}  {'to 1st token':>12}  {'llm total':>9}  {'total':>6}  gate")
    best = None
    for r in rows:
        recall_ok = (r["metrics"]["context_recall"] or 0) >= 0.999
        faith_ok = (r["metrics"]["faithfulness"] or 0) >= FAITHFULNESS_MIN
        ok = recall_ok and faith_ok and r["failed"] == 0
        verdict = "PASS" if ok else "FAIL (" + ", ".join(
            reason for reason, bad in (("recall<1", not recall_ok), ("faithfulness<0.95", not faith_ok), ("failed samples", r["failed"] > 0)) if bad
        ) + ")"
        print(f"{r['k']:>4}  {_fmt(r['retrieval'], 1000, 2):>9}  {_fmt(r['ttft'], 1000, 2):>12}  {_fmt(r['llm'], 1000, 2):>9}  {_fmt(r['total'], 1000, 2):>6}  {verdict}")
        if ok and r["total"] is not None and (best is None or r["total"] < best["total"]):
            best = r
    print()
    if best:
        print(f"Fastest run that passes the gate: K={best['k']} ({best['file']}).")
        print("Latency differences between runs of a few hundred ms are within network noise; prefer the larger K unless the gain is clear.")
    else:
        print("No run passed the gate.")


if __name__ == "__main__":
    main()
