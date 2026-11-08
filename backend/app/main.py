
import hmac
import logging
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.rag import stream_answer


logger = logging.getLogger("portfolio_api")


def client_key(request: Request) -> str:
    """Identify visitors for rate limiting."""
    return (
        request.headers.get("x-client-ip")
        or get_remote_address(request)
    )


limiter = Limiter(key_func=client_key)

app = FastAPI(
    title="Touqeer Ali Portfolio RAG API",
    version="3.0.0",
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=500)


class ChatRequest(BaseModel):
    messages: list[Message] = Field(
        min_length=1,
        max_length=12,
    )


@app.get("/health")
def health() -> dict[str, str]:
    """Check whether the backend API is running."""
    return {
        "status": "ok",
        "service": "portfolio-rag-api",
    }


@app.post("/chat")
@limiter.limit("10/minute;80/day")
def chat(
    request: Request,
    body: ChatRequest,
    x_api_key: str = Header(default=""),
) -> StreamingResponse:
    """Authenticate the request and stream the RAG response."""

    # 1. Verify shared secret.
    if not hmac.compare_digest(
        x_api_key.encode("utf-8"),
        settings.shared_secret.encode("utf-8"),
    ):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
        )

    # 2. Last message must be from the visitor.
    if body.messages[-1].role != "user":
        raise HTTPException(
            status_code=400,
            detail="Last message must be from user",
        )

    # 3. Convert Pydantic models into dictionaries.
    messages = [
        message.model_dump()
        for message in body.messages
    ]

    # 4. Stream the LangChain RAG response.
    return StreamingResponse(
        stream_answer(messages),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )
