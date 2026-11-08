
"""Hybrid Qdrant retriever using dense search, BM25 and RRF."""

from functools import lru_cache
from typing import Any

from pydantic import ConfigDict, Field
from qdrant_client import QdrantClient, models

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from app.config import settings
from app.providers import embed_query


def create_qdrant_client() -> QdrantClient:
    """Create a Qdrant Cloud client."""
    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        timeout=30,
    )


class QdrantHybridRetriever(BaseRetriever):
    """Retrieve documents using dense search + BM25 + RRF."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    collection_name: str = settings.hybrid_collection

    dense_top_k: int = settings.dense_top_k
    bm25_top_k: int = settings.bm25_top_k
    result_limit: int = settings.rrf_limit
    rrf_k: int = settings.rrf_k

    client: Any = Field(
        default_factory=create_qdrant_client,
        exclude=True,
    )

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:
        """Execute dense + BM25 searches and combine them using RRF."""

        query = query.strip()

        if not query:
            return []

        # 1. Generate dense query embedding through LangChain.
        dense_vector = embed_query(query)

        # 2. Prepare dense semantic search.
        dense_prefetch = models.Prefetch(
            query=dense_vector,
            limit=self.dense_top_k,
        )

        # 3. Prepare BM25 keyword search.
        bm25_prefetch = models.Prefetch(
            query=models.TextQuery(text=query),
            using="text",
            limit=self.bm25_top_k,
        )

        # 4. Execute both searches and fuse their rankings with RRF.
        response = self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                dense_prefetch,
                bm25_prefetch,
            ],
            query=models.RrfQuery(
                rrf=models.Rrf(k=self.rrf_k),
            ),
            limit=self.result_limit,
            with_payload=True,
        )

        # 5. Convert Qdrant results into LangChain Documents.
        documents: list[Document] = []

        for point in response.points:
            payload = point.payload or {}
            text = payload.get("text")

            if not isinstance(text, str) or not text.strip():
                continue

            metadata = {
                key: value
                for key, value in payload.items()
                if key != "text"
            }

            metadata["qdrant_id"] = str(point.id)
            metadata["retrieval_method"] = "hybrid_rrf"
            metadata["retrieval_score"] = float(point.score)

            documents.append(
                Document(
                    page_content=text,
                    metadata=metadata,
                )
            )

        return documents


@lru_cache(maxsize=1)
def get_hybrid_retriever() -> QdrantHybridRetriever:
    """Return one cached hybrid retriever instance."""

    return QdrantHybridRetriever(
        collection_name=settings.hybrid_collection,
        dense_top_k=settings.dense_top_k,
        bm25_top_k=settings.bm25_top_k,
        result_limit=settings.rrf_limit,
        rrf_k=settings.rrf_k,
    )
