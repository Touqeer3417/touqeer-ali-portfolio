"""End-to-end streaming behaviour of the chat backend.

Covers, without calling OpenAI or Qdrant:
  * tokens leave ``stream_answer`` as the model produces them (no buffering),
  * the model stream is closed on early close, cancellation and errors,
  * a mid-stream failure keeps the partial answer and appends the apology,
  * over real HTTP (uvicorn on a loopback port) chunks reach the client
    progressively, headers disable proxy buffering, and a client disconnect
    cancels the server-side generator so cleanup runs.

Run from ``backend``: ``python -m unittest tests.test_streaming -v``
"""

from __future__ import annotations

import asyncio
import socket
import threading
import time
import unittest
from typing import Any, AsyncIterator
from unittest.mock import AsyncMock, patch

import httpx
import uvicorn
from langchain_core.documents import Document
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult

from app import rag
from app.config import settings
from app.main import app
from app.response_cache import response_cache


class FakeStreamingModel(BaseChatModel):
    """Chat model that emits ``tokens`` with a delay and records its lifecycle."""

    tokens: list[str]
    delay: float = 0.05
    fail_after: int | None = None
    state: Any = None  # shared dict owned by the test (Any avoids pydantic copying it)

    @property
    def _llm_type(self) -> str:
        return "fake-streaming"

    def _generate(self, messages: list[BaseMessage], stop=None, run_manager=None, **kwargs: Any) -> ChatResult:
        text = "".join(self.tokens)
        return ChatResult(generations=[ChatGeneration(message=AIMessageChunk(content=text))])

    async def _astream(
        self, messages: list[BaseMessage], stop=None, run_manager=None, **kwargs: Any
    ) -> AsyncIterator[ChatGenerationChunk]:
        self.state["finished"] = False
        try:
            for index, token in enumerate(self.tokens):
                if self.fail_after is not None and index == self.fail_after:
                    raise RuntimeError("simulated upstream failure")
                await asyncio.sleep(self.delay)
                yield ChatGenerationChunk(message=AIMessageChunk(content=token))
            self.state["finished"] = True
        finally:
            self.state["closed"] = True


DOCUMENT = Document(page_content="Touqeer builds RAG systems.", metadata={"source_filename": "about.md"})
MESSAGES = [{"role": "user", "content": "What does Touqeer build?"}]


async def wait_for_flag(state: dict[str, Any], key: str, timeout: float = 1.0) -> bool:
    """Give the event loop a moment: nested async generators finalize via the loop."""
    deadline = time.perf_counter() + timeout
    while not state.get(key) and time.perf_counter() < deadline:
        await asyncio.sleep(0.01)
    return bool(state.get(key))


def run_stream(model: FakeStreamingModel):
    """Patch retrieval and the model, then return the ``stream_answer`` generator."""
    patches = (
        patch.object(rag, "aretrieve_documents", AsyncMock(return_value=[DOCUMENT])),
        patch.object(rag, "get_chat_model", lambda: model),
    )
    for p in patches:
        p.start()
    return rag.stream_answer(MESSAGES), patches


class StreamAnswerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.state: dict[str, Any] = {}
        self.patches: tuple = ()
        # Every test here drives the model through the same question; a cached
        # answer would short-circuit the stream being asserted on.
        response_cache.clear()

    async def asyncTearDown(self) -> None:
        for p in self.patches:
            p.stop()

    def model(self, **kwargs: Any) -> FakeStreamingModel:
        return FakeStreamingModel(state=self.state, **kwargs)

    async def test_tokens_are_yielded_while_the_model_is_still_generating(self) -> None:
        stream, self.patches = run_stream(self.model(tokens=["Hello", " ", "world", "!"], delay=0.05))
        arrivals: list[tuple[float, str, bool]] = []
        started = time.perf_counter()
        async for chunk in stream:
            arrivals.append((time.perf_counter() - started, chunk, bool(self.state.get("finished"))))

        self.assertEqual("".join(c for _, c, _ in arrivals), "Hello world!")
        self.assertGreaterEqual(len(arrivals), 4)
        # First token is delivered long before the last one and before the model ends.
        self.assertFalse(arrivals[0][2], "first chunk arrived only after generation finished")
        self.assertGreater(arrivals[-1][0] - arrivals[0][0], 0.1)

    async def test_closing_the_stream_early_closes_the_model_stream(self) -> None:
        stream, self.patches = run_stream(self.model(tokens=["a"] * 50, delay=0.02))
        self.assertEqual(await anext(stream), "a")
        await stream.aclose()

        self.assertTrue(await wait_for_flag(self.state, "closed"), "model stream was not closed")
        self.assertFalse(self.state.get("finished"), "model kept generating after close")

    async def test_cancellation_closes_the_model_stream(self) -> None:
        stream, self.patches = run_stream(self.model(tokens=["a"] * 200, delay=0.02))
        first_token = asyncio.Event()

        async def consume() -> None:
            async for _ in stream:
                first_token.set()

        task = asyncio.create_task(consume())
        await asyncio.wait_for(first_token.wait(), timeout=2)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task

        self.assertTrue(await wait_for_flag(self.state, "closed"), "model stream was not closed on cancel")
        self.assertFalse(self.state.get("finished"))

    async def test_mid_stream_failure_keeps_partial_answer_and_adds_apology(self) -> None:
        stream, self.patches = run_stream(self.model(tokens=["Partial", " answer", " never", " sent"], delay=0.01, fail_after=2))
        chunks = [chunk async for chunk in stream]
        text = "".join(chunks)

        self.assertTrue(text.startswith("Partial answer"))
        self.assertIn("\n\nSorry, something went wrong", text)
        self.assertNotIn("never", text)
        self.assertTrue(self.state.get("closed"))

    async def test_failure_before_any_token_has_no_leading_blank_lines(self) -> None:
        stream, self.patches = run_stream(self.model(tokens=["x"], delay=0.01, fail_after=0))
        text = "".join([chunk async for chunk in stream])

        self.assertTrue(text.startswith("Sorry, something went wrong"))


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class HttpStreamingTests(unittest.TestCase):
    """Real HTTP over loopback: TestClient buffers bodies, so it can't prove streaming."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.port = free_port()
        cls.url = f"http://127.0.0.1:{cls.port}"
        config = uvicorn.Config(app, host="127.0.0.1", port=cls.port, log_level="warning", lifespan="off")
        cls.server = uvicorn.Server(config)
        cls.thread = threading.Thread(target=cls.server.run, daemon=True)
        cls.thread.start()
        deadline = time.time() + 10
        while not cls.server.started and time.time() < deadline:
            time.sleep(0.02)
        if not cls.server.started:
            raise RuntimeError("uvicorn did not start")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.should_exit = True
        cls.thread.join(timeout=5)

    def setUp(self) -> None:
        app.state.limiter.reset()
        self.headers = {"x-api-key": settings.shared_secret}
        self.body = {"messages": [{"role": "user", "content": "hi"}]}

    def test_chunks_reach_the_client_progressively(self) -> None:
        async def fake_stream(_messages: list[dict]) -> AsyncIterator[str]:
            for token in ["one ", "two ", "three ", "four"]:
                await asyncio.sleep(0.15)
                yield token

        arrivals: list[tuple[float, bytes]] = []
        with patch("app.main.stream_answer", fake_stream):
            started = time.perf_counter()
            with httpx.Client(timeout=10) as client:
                with client.stream("POST", f"{self.url}/chat", json=self.body, headers=self.headers) as response:
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.headers["cache-control"], "no-cache, no-transform")
                    self.assertEqual(response.headers["x-accel-buffering"], "no")
                    self.assertTrue(response.headers["x-request-id"])
                    self.assertTrue(response.headers["content-type"].startswith("text/plain"))
                    for chunk in response.iter_raw():
                        arrivals.append((time.perf_counter() - started, chunk))

        self.assertEqual(b"".join(c for _, c in arrivals), b"one two three four")
        self.assertGreaterEqual(len(arrivals), 3, "body was delivered in too few pieces (buffered?)")
        self.assertLess(arrivals[0][0], 0.45, "first chunk was held back until the end")
        self.assertGreater(arrivals[-1][0] - arrivals[0][0], 0.3)

    def test_client_disconnect_cancels_the_server_generator(self) -> None:
        cleaned_up = threading.Event()

        async def endless_stream(_messages: list[dict]) -> AsyncIterator[str]:
            try:
                while True:
                    await asyncio.sleep(0.05)
                    yield "tok "
            finally:
                cleaned_up.set()

        with patch("app.main.stream_answer", endless_stream):
            with httpx.Client(timeout=10) as client:
                with client.stream("POST", f"{self.url}/chat", json=self.body, headers=self.headers) as response:
                    iterator = response.iter_raw()
                    self.assertTrue(next(iterator))
                # leaving the context closes the connection mid-stream

            self.assertTrue(cleaned_up.wait(timeout=5), "server generator kept running after client disconnect")

    def test_rejects_a_bad_api_key_before_streaming(self) -> None:
        response = httpx.post(f"{self.url}/chat", json=self.body, headers={"x-api-key": "wrong"}, timeout=10)
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
