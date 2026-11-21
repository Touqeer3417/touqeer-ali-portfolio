
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    # OpenAI configuration
    openai_api_key: str
    embed_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4o-mini"

    # Qdrant configuration
    qdrant_url: str
    qdrant_api_key: str

    # Existing collection (preserved)
    collection: str = "portfolio_kb"

    # New hybrid collection
    hybrid_collection: str = "portfolio_kb_hybrid"

    # Dense retrieval settings
    dense_top_k: int = 10

    # BM25 retrieval settings
    bm25_top_k: int = 10

    # Final hybrid results
    rrf_limit: int = 5

    # Qdrant Reciprocal Rank Fusion
    rrf_k: int = 2

    # Seconds idle upstream connections stay open (httpx default is 5). 0 = library default.
    http_keepalive_expiry: float = Field(default=60.0, ge=0.0)

    # Bounded LRU of query embeddings (0 disables).
    embedding_cache_size: int = Field(default=256, ge=0)

    # Background warm-up at server start (BM25 prebuild, starter-question embeddings, connections).
    warmup_enabled: bool = True
    warmup_llm: bool = True  # one 1-token completion; set false to avoid any token spend
    warmup_queries: list[str] = [
        "What has Touqeer built?",
        "Can he build a RAG chatbot for my business?",
        "Touqeer ki skills kya hain?",
        "How can I contact him?",
    ]

    # Existing API settings
    shared_secret: str = Field(min_length=24)
    top_k: int = 5

    # Ingestion configuration
    knowledge_dir: Path = APP_DIR.parent / "knowledge"
    chunk_size: int = Field(default=800, ge=100)
    chunk_overlap: int = Field(default=120, ge=0)
    ingestion_batch_size: int = Field(default=64, ge=1)
    bm25_index_path: Path = APP_DIR.parent / ".rag-index" / "bm25-documents.json"

    # Hybrid retrieval configuration
    dense_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    bm25_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    reranker_enabled: bool = False
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    reranker_candidate_k: int = Field(default=10, ge=1)

    @model_validator(mode="after")
    def validate_rag_settings(self):
        """Reject configurations that cannot produce a valid chunk or fusion."""
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        if self.dense_weight + self.bm25_weight <= 0:
            raise ValueError("At least one hybrid retrieval weight must be greater than zero")
        return self


settings = Settings()
