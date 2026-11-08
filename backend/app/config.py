from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str
    qdrant_url: str
    qdrant_api_key: str
    collection: str = "portfolio_kb"
    embed_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4o-mini"  # change in .env to any cheap chat model you have access to
    shared_secret: str = ""  # must match RAG_API_SECRET in the Next.js app
    top_k: int = 5


settings = Settings()
