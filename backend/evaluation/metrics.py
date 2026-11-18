"""RAGAS v0.4 collection metrics using the application's configured clients."""

from __future__ import annotations

import math
from typing import Any

from evaluation.config import METRIC_NAMES


def build_metrics() -> dict[str, Any]:
    """Create the five real RAGAS metrics around the existing LLM/embeddings."""
    from ragas.embeddings import embedding_factory
    from ragas.llms import llm_factory
    from ragas.metrics.collections import (
        AnswerCorrectness,
        AnswerRelevancy,
        ContextPrecision,
        ContextRecall,
        Faithfulness,
    )

    from app.config import settings
    from app.providers import get_chat_model, get_embeddings
    from openai import AsyncOpenAI

    # RAGAS 0.4 collection metrics require modern structured-output and
    # embedding interfaces. Reuse the configured chat client's async transport
    # and the embedding model/client configured by the application.
    chat_model = get_chat_model()
    llm = llm_factory(
        settings.chat_model,
        client=chat_model.root_async_client,
        temperature=0,
    )
    existing_embeddings = get_embeddings()
    embedding_client = AsyncOpenAI(api_key=settings.openai_api_key)
    embeddings = embedding_factory(
        provider="openai",
        model=existing_embeddings.model,
        client=embedding_client,
    )
    return {
        "answer_correctness": AnswerCorrectness(llm=llm, embeddings=embeddings),
        "answer_relevancy": AnswerRelevancy(llm=llm, embeddings=embeddings),
        "faithfulness": Faithfulness(llm=llm),
        "context_recall": ContextRecall(llm=llm),
        "context_precision": ContextPrecision(llm=llm),
    }


async def score_sample(
    *,
    user_input: str,
    response: str,
    retrieved_contexts: list[str],
    reference: str | None,
    metrics: dict[str, Any] | None = None,
) -> tuple[dict[str, float | None], dict[str, str]]:
    """Run the supported RAGAS metric APIs; failures remain explicit as null."""
    instances = metrics or build_metrics()
    inputs = {
        "answer_correctness": {"user_input": user_input, "response": response, "reference": reference},
        "answer_relevancy": {"user_input": user_input, "response": response},
        "faithfulness": {"user_input": user_input, "response": response, "retrieved_contexts": retrieved_contexts},
        "context_recall": {"user_input": user_input, "retrieved_contexts": retrieved_contexts, "reference": reference},
        "context_precision": {"user_input": user_input, "retrieved_contexts": retrieved_contexts, "reference": reference},
    }
    scores: dict[str, float | None] = {name: None for name in METRIC_NAMES}
    errors: dict[str, str] = {}

    reference_metrics = {"answer_correctness", "context_recall", "context_precision"}
    if not reference:
        for name in reference_metrics:
            errors[name] = "Not evaluated: ground-truth reference is missing."

    for name in METRIC_NAMES:
        if name in reference_metrics and not reference:
            continue
        try:
            result = await instances[name].ascore(**inputs[name])
            value = float(result.value)
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"RAGAS returned an invalid score: {value}")
            scores[name] = value
        except Exception as exc:
            errors[name] = f"{type(exc).__name__}: {exc}"
    return scores, errors
