"""Optional Cross-Encoder reranking, disabled unless explicitly configured."""

from __future__ import annotations

import logging
from functools import lru_cache
import math
from time import perf_counter

from langchain_core.documents import Document

from app.config import settings
from app.latency import record_stage, set_flag


logger = logging.getLogger("rag")


@lru_cache(maxsize=1)
def _cross_encoder():
    try:
        from sentence_transformers import CrossEncoder
    except ImportError as exc:
        raise RuntimeError(
            "RERANKER_ENABLED=true requires the optional backend/requirements-reranker.txt package."
        ) from exc
    # Runs only on the lru_cache miss: this request paid for loading the model.
    set_flag("cross_encoder_cold")
    return CrossEncoder(settings.reranker_model)


def rerank_documents(query: str, documents: list[Document]) -> list[Document]:
    """Order leading RRF candidates by Cross-Encoder relevance, falling back on error."""
    if not settings.reranker_enabled or not documents:
        return documents

    candidates = documents[: settings.reranker_candidate_k]
    started = perf_counter()
    try:
        model = _cross_encoder()
        pairs = []
        for document in candidates:
            project_name = document.metadata.get("project_name")
            section_heading = document.metadata.get("section_heading")
            labels = [
                f"Project: {project_name}" if project_name else None,
                f"Section: {section_heading}" if section_heading else None,
            ]
            metadata_context = " | ".join(label for label in labels if label)
            document_text = (
                f"{metadata_context}\n{document.page_content}"
                if metadata_context
                else document.page_content
            )
            pairs.append([query, document_text])
        raw_scores = model.predict(pairs)
        scores = [float(score) for score in raw_scores]
        if len(scores) != len(candidates) or not all(math.isfinite(score) for score in scores):
            raise ValueError("Cross-Encoder returned an invalid number of relevance scores")

        reranked = [
            document
            for _, document in sorted(
                zip(scores, candidates), key=lambda pair: pair[0], reverse=True
            )
        ]
        for document, score in zip(candidates, scores):
            document.metadata["reranker_score"] = score
            document.metadata["retrieval_method"] = "hybrid_rrf_cross_encoder"
        reranked.extend(documents[len(candidates):])
        logger.info(
            "rag_stage stage=reranking duration_ms=%.1f candidates=%d model=%s",
            (perf_counter() - started) * 1000,
            len(candidates),
            settings.reranker_model,
        )
        return reranked
    except Exception:
        logger.exception(
            "Cross-Encoder reranking failed; preserving original hybrid order model=%s",
            settings.reranker_model,
        )
        logger.info(
            "rag_stage stage=reranking_fallback duration_ms=%.1f candidates=%d",
            (perf_counter() - started) * 1000,
            len(candidates),
        )
        return documents
    finally:
        record_stage("reranking_ms", (perf_counter() - started) * 1000)
