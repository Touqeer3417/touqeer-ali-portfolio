
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

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

    # Existing API settings
    shared_secret: str = Field(min_length=24)
    top_k: int = 5


settings = Settings()
