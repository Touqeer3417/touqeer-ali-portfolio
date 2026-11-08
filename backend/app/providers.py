
from functools import lru_cache

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.config import settings


@lru_cache(maxsize=1)
def get_chat_model() -> ChatOpenAI:
    """
    Initialize and cache the LangChain chat model.
    Used for generating portfolio chatbot responses.
    """
    return ChatOpenAI(
        model=settings.chat_model,
        api_key=settings.openai_api_key,
        temperature=0.3,
        max_tokens=350,
        max_retries=2,
    )


@lru_cache(maxsize=1)
def get_embeddings() -> OpenAIEmbeddings:
    """
    Initialize and cache OpenAI embeddings through LangChain.
    Used for dense vector generation.
    """
    return OpenAIEmbeddings(
        model=settings.embed_model,
        api_key=settings.openai_api_key,
        max_retries=2,
    )


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple documents."""
    if not texts:
        return []

    return get_embeddings().embed_documents(texts)


def embed_query(text: str) -> list[float]:
    """Generate an embedding for a search query."""
    return get_embeddings().embed_query(text)
