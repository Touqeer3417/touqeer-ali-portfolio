
import asyncio
import hmac
import logging
import uuid
from contextlib import aclosing, asynccontextmanager, suppress
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Path, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, model_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.latency import get_record, public_latency, use_request_id
from app.rag import stream_answer
from app.response_cache import response_cache
from app.warmup import warm_up


logger = logging.getLogger("portfolio_api")


def client_key(request: Request) -> str:
    """Identify visitors for rate limiting."""
    return (
        request.headers.get("x-client-ip")
        or get_remote_address(request)
    )


limiter = Limiter(key_func=client_key)

@asynccontextmanager
async def lifespan(_: FastAPI):
    """Warm caches and connections in the background; never delays /health."""
    task = asyncio.create_task(warm_up()) if settings.warmup_enabled else None
    try:
        yield
    finally:
        if task is not None and not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


app = FastAPI(
    title="Touqeer Ali Portfolio RAG API",
    version="3.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=5000)

    @model_validator(mode="after")
    def limit_user_input(self) -> "Message":
        """Keep visitor input bounded while allowing full assistant history."""
        if self.role == "user" and len(self.content) > 500:
            raise ValueError("User messages cannot exceed 500 characters")
        return self


class ChatRequest(BaseModel):
    messages: list[Message] = Field(
        min_length=1,
        max_length=12,
    )


async def _stream_with_request_id(messages: list[dict], request_id: str):
    """Run the unchanged RAG stream under a known request id.

    ``aclosing`` guarantees the inner generator's ``finally`` (latency record,
    logging) runs even if the client disconnects mid-stream.
    """
    with use_request_id(request_id):
        try:
            async with aclosing(stream_answer(messages)) as stream:
                async for chunk in stream:
                    yield chunk
        except asyncio.CancelledError:
            # Starlette cancels the response task when the client disconnects
            # (browser Stop, tab close, proxy abort). Cleanup already ran in the
            # inner ``finally`` blocks; re-raise so cancellation propagates.
            logger.info("chat stream cancelled by client request_id=%s", request_id)
            raise


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

    # 4. Stream the LangChain RAG response. The request id is known before the
    # first byte, so it travels as a header; the response body is unchanged.
    request_id = uuid.uuid4().hex[:16]
    return StreamingResponse(
        _stream_with_request_id(messages, request_id),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "X-Request-ID": request_id,
        },
    )


@app.get("/latency/{request_id}")
@limiter.limit("60/minute")
def latency(
    request: Request,
    request_id: str = Path(min_length=1, max_length=64),
    x_api_key: str = Header(default=""),
) -> dict[str, object]:
    """Return stage timings for a finished /chat request (same secret as /chat).

    Records live in a bounded in-process window (last 1000 requests), so this is
    reliable for a single worker; call it after the stream has completed.
    """
    if not hmac.compare_digest(
        x_api_key.encode("utf-8"),
        settings.shared_secret.encode("utf-8"),
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")

    record = get_record(request_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Latency record not found")
    return {"latency_ms": public_latency(record)}


@app.get("/cache/stats")
@limiter.limit("60/minute")
def cache_stats(
    request: Request,
    x_api_key: str = Header(default=""),
) -> dict[str, object]:
    """Return response-cache counters for this worker (same secret as /chat).

    Counters are per process and reset on restart, so with several workers this
    reports the one that served the request. No visitor content is exposed.
    """
    if not hmac.compare_digest(
        x_api_key.encode("utf-8"),
        settings.shared_secret.encode("utf-8"),
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")

    return {"response_cache": response_cache.stats()}
