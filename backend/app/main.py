import hmac
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.rag import stream_answer


def client_key(request: Request) -> str:
    # The Next.js proxy forwards the real visitor IP. Safe to trust: /chat also needs the shared secret.
    return request.headers.get("x-client-ip") or get_remote_address(request)


limiter = Limiter(key_func=client_key)
app = FastAPI(title="Portfolio RAG API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class Msg(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    messages: list[Msg] = Field(min_length=1, max_length=12)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
@limiter.limit("10/minute;80/day")
def chat(request: Request, body: ChatRequest, x_api_key: str = Header(default="")):
    if settings.shared_secret and not hmac.compare_digest(
        x_api_key.encode(), settings.shared_secret.encode()
    ):
        raise HTTPException(status_code=401, detail="unauthorized")

    last = body.messages[-1]
    if last.role != "user":
        raise HTTPException(status_code=400, detail="last message must be from user")
    if len(last.content) > 500:
        raise HTTPException(status_code=400, detail="message too long (max 500 chars)")

    messages = [m.model_dump() for m in body.messages]
    return StreamingResponse(
        stream_answer(messages), media_type="text/plain; charset=utf-8"
    )
