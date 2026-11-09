import logging
from types import SimpleNamespace

import pytest

from app import rag


def test_retrieval_query_uses_the_last_two_user_turns_only():
    messages = [
        {"role": "user", "content": "Tell me about Corrective RAG."},
        {"role": "assistant", "content": "It is a retrieval system."},
        {"role": "user", "content": "Which vector database does it use?"},
    ]

    assert rag.retrieval_query(messages) == (
        "Tell me about Corrective RAG. Which vector database does it use?"
    )


def test_retrieval_query_ignores_empty_user_messages():
    assert rag.retrieval_query(
        [
            {"role": "user", "content": "  "},
            {"role": "assistant", "content": "Hello"},
        ]
    ) == ""


def test_format_context_preserves_document_sources_and_chunk_ids():
    documents = [
        SimpleNamespace(
            page_content="Corrective RAG uses Qdrant and BM25.",
            metadata={"source": "projects.md", "chunk_index": 1},
        ),
        SimpleNamespace(
            page_content="Touqeer studies Software Engineering.",
            metadata={"source": "about.md", "chunk_index": 0},
        ),
    ]

    context, sources = rag.format_context(documents)

    assert "[Source: projects.md | Chunk: 1]" in context
    assert "Corrective RAG uses Qdrant and BM25." in context
    assert "- about.md" in sources
    assert "- projects.md" in sources


def test_build_history_keeps_only_the_last_eight_messages():
    messages = [
        {"role": "user", "content": f"question {index}"}
        if index % 2 == 0
        else {"role": "assistant", "content": f"answer {index}"}
        for index in range(10)
    ]

    history = rag.build_history(messages)

    assert len(history) == 8
    assert history[0].content == "question 2"
    assert history[-1].content == "answer 9"


def test_stream_answer_returns_explicit_fallback_when_retrieval_is_empty(monkeypatch, caplog):
    monkeypatch.setattr(rag, "retrieve_documents", lambda query: [])

    with caplog.at_level(logging.INFO, logger="rag"):
        answer = "".join(
            rag.stream_answer([{"role": "user", "content": "What is Touqeer's salary?"}])
        )

    assert "could not find that information" in answer.lower()
    assert "outcome=no_documents" in caplog.text
    assert "rag_timing" in caplog.text


def test_stream_answer_uses_retrieved_evidence_and_streams_model_output(monkeypatch):
    document = SimpleNamespace(
        page_content="Corrective RAG uses Qdrant and BM25.",
        metadata={"source": "projects.md", "chunk_index": 1},
    )

    class FakeChain:
        def stream(self, values):
            assert "Qdrant and BM25" in values["context"]
            assert "projects.md" in values["sources"]
            yield SimpleNamespace(content="Corrective RAG uses ")
            yield SimpleNamespace(content="Qdrant and BM25.")

    class FakePrompt:
        def __or__(self, model):
            return FakeChain()

    monkeypatch.setattr(rag, "retrieve_documents", lambda query: [document])
    monkeypatch.setattr(rag.ChatPromptTemplate, "from_messages", lambda messages: FakePrompt())
    monkeypatch.setattr(rag, "get_chat_model", lambda: object())

    answer = "".join(
        rag.stream_answer([{"role": "user", "content": "What database does Corrective RAG use?"}])
    )

    assert answer == "Corrective RAG uses Qdrant and BM25."
