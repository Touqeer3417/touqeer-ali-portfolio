from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from langchain_core.documents import Document

from app.config import settings
from app.retrieval.reranker import rerank_documents


class RerankerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.documents = [
            Document(page_content="generic profile", metadata={"chunk_id": "generic"}),
            Document(page_content="RAG project using hybrid search", metadata={"chunk_id": "rag"}),
            Document(page_content="Contact details", metadata={"chunk_id": "contact"}),
        ]

    def test_enabled_cross_encoder_reorders_by_relevance(self) -> None:
        model = Mock()
        model.predict.return_value = [0.1, 0.95, 0.2]
        with patch.object(settings, "reranker_enabled", True), patch(
            "app.retrieval.reranker._cross_encoder", return_value=model
        ):
            result = rerank_documents("What RAG project was built?", self.documents)

        self.assertEqual([doc.metadata["chunk_id"] for doc in result], ["rag", "contact", "generic"])
        self.assertEqual(result[0].metadata["reranker_score"], 0.95)
        self.assertEqual(result[0].metadata["retrieval_method"], "hybrid_rrf_cross_encoder")
        model.predict.assert_called_once_with([
            ["What RAG project was built?", document.page_content]
            for document in self.documents
        ])

    def test_disabled_reranker_preserves_results_without_loading_model(self) -> None:
        with patch.object(settings, "reranker_enabled", False), patch(
            "app.retrieval.reranker._cross_encoder"
        ) as load_model:
            result = rerank_documents("query", self.documents)

        self.assertIs(result, self.documents)
        load_model.assert_not_called()

    def test_scoring_failure_falls_back_to_original_hybrid_order(self) -> None:
        model = Mock()
        model.predict.side_effect = RuntimeError("model unavailable")
        with patch.object(settings, "reranker_enabled", True), patch(
            "app.retrieval.reranker._cross_encoder", return_value=model
        ):
            result = rerank_documents("query", self.documents)

        self.assertIs(result, self.documents)
        self.assertEqual([doc.metadata["chunk_id"] for doc in result], ["generic", "rag", "contact"])
        self.assertTrue(all("reranker_score" not in doc.metadata for doc in result))


if __name__ == "__main__":
    unittest.main()
