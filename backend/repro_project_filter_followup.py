"""Offline repro for F1: a project named in an EARLIER turn locked retrieval to that project.

Run from the backend folder (PowerShell):  python repro_project_filter_followup.py
Needs only the app's own dependencies and the usual .env (no network calls are made).
Prints the OLD behaviour (joined last-two-turns query + project from that text) next to
the NEW behaviour (plan_scope) for several follow-up questions.
"""
import tempfile
from pathlib import Path

from langchain_core.documents import Document

from app.ingestion.state import IndexSnapshot, write_snapshot
from app.rag import retrieval_query
from app.retrieval.document_awareness import plan_scope, resolve_project
from app.retrieval.sparse import BM25Index

docs = [
    Document(page_content="Corrective RAG uses Qdrant, LangGraph and Groq. Tech stack and architecture.", metadata={"chunk_id": "c1", "project_id": "corrective-rag", "project_name": "Corrective RAG", "source_filename": "projects.md"}),
    Document(page_content="Corrective RAG limitations: public deployment is not confirmed.", metadata={"chunk_id": "c2", "project_id": "corrective-rag", "project_name": "Corrective RAG", "source_filename": "projects.md"}),
    Document(page_content="Document Search RAG uses ChromaDB, FAISS and BM25.", metadata={"chunk_id": "c3", "project_id": "document-search-rag", "project_name": "Document Search RAG", "source_filename": "projects.md"}),
    Document(page_content="Email: touqeerali3417@gmail.com contact LinkedIn for project inquiries and hiring.", metadata={"chunk_id": "k1", "source_filename": "contact.md"}),
    Document(page_content="Services: custom RAG chatbots and full-stack development.", metadata={"chunk_id": "s1", "source_filename": "services.md"}),
    Document(page_content="Skills: Python, FastAPI, LangChain, Qdrant, React.", metadata={"chunk_id": "k2", "source_filename": "skills.md"}),
]
FIRST = "Tell me about Touqeer's Corrective RAG project"
CASES = [
    ("contact follow-up", [FIRST, "How can I contact him for a project?"]),
    ("services follow-up", [FIRST, "What services does he offer?"]),
    ("skills follow-up", [FIRST, "What skills does he have?"]),
    ("'What stack does it use?'", [FIRST, "What stack does it use?"]),
    ("'What are its limitations?'", [FIRST, "What are its limitations?"]),
    ("switch project", ["Tell me about the Document Search RAG project", "What about Corrective RAG?"]),
]


def bm25_sources(index: BM25Index, project, query: str) -> list[str]:
    found = index.retriever(project[0] if project else None).invoke(query)
    return [d.metadata["source_filename"] + (f"[{d.metadata['project_id']}]" if d.metadata.get("project_id") else "") for d in found][:3]


with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / "index.json"
    write_snapshot(IndexSnapshot(docs, {}, set()), path)
    index = BM25Index(path)
    for title, turns in CASES:
        messages = []
        for i, turn in enumerate(turns):
            messages += ([{"role": "assistant", "content": "..."}] if i else []) + [{"role": "user", "content": turn}]
        old_query = retrieval_query(messages)
        old_project = resolve_project(old_query, docs)
        plan = plan_scope(turns[-1], turns[:-1], docs)
        print(f"\n== {title}: {turns[-1]!r}")
        print(f"   OLD scope={old_project[0] if old_project else None!s:<20} top BM25 -> {bm25_sources(index, old_project, old_query)}")
        print(f"   NEW scope={plan.project[0] if plan.project else None!s:<20} top BM25 -> {bm25_sources(index, plan.project, plan.query)}   ({plan.reason})")
