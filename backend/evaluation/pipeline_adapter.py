"""Non-invasive adapter that captures outputs from the real application flow."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

from langchain_core.documents import Document


GENERATION_ERROR = "Sorry, something went wrong while processing your question. Please try again in a moment."
NO_CONTEXT_RESPONSE = "I could not find that information in Touqeer's portfolio knowledge base. Please contact him directly."


@dataclass(frozen=True)
class PipelineOutput:
    response: str
    retrieved_contexts: list[str]
    status: str = "complete"
    error: str | None = None
    retrieval_trace: dict | None = None


async def run_existing_pipeline(user_input: str) -> PipelineOutput:
    """Call ``app.rag.stream_answer`` and capture its actual retrieved chunks.

    The evaluation runner is a separate process, so a scoped patch around the
    existing retrieval function can observe documents without changing app code.
    The existing prompt, retrieval, generation, and streaming behavior remain in use.
    """
    from app import rag

    captured_documents: list[Document] = []
    captured_trace: dict | None = None
    existing_retrieval = rag.aretrieve_documents

    async def capture_retrieval(query: str):
        nonlocal captured_trace
        documents = await existing_retrieval(query)
        captured_documents.extend(documents)
        from app.retrieval.trace import get_retrieval_trace

        captured_trace = get_retrieval_trace()
        return documents

    messages = [{"role": "user", "content": user_input}]
    with patch.object(rag, "aretrieve_documents", side_effect=capture_retrieval):
        response_parts = [part async for part in rag.stream_answer(messages)]

    response = "".join(response_parts).strip()
    contexts = [document.page_content for document in captured_documents]
    if response == GENERATION_ERROR:
        return PipelineOutput(response, contexts, "failed", "Existing RAG generation returned its error fallback", captured_trace)
    if not contexts or response == NO_CONTEXT_RESPONSE:
        return PipelineOutput(response, contexts, "incomplete", "Existing retriever returned no usable context", captured_trace)
    if not response:
        return PipelineOutput("", contexts, "failed", "Existing RAG pipeline returned an empty response", captured_trace)
    return PipelineOutput(response, contexts, retrieval_trace=captured_trace)
