"""Thin async client for talking to the underlying llama.cpp server.

This is the only module that knows llama-server's address. Everything else
in the API talks to functions here, so swapping the inference backend later
(e.g. to vLLM) only touches this file.

Includes retry-with-backoff for transient failures (connection errors,
timeouts, upstream 5xx) so a brief llama-server hiccup - a GC pause, a
model reload, a momentary resource spike - doesn't surface as a hard
failure to the caller. Retries are NOT applied to streaming responses,
since partial output may have already been sent to the client by the time
a failure occurs.
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx

from server.core.config import settings

logger = logging.getLogger("anvilllm.llama_client")


class LlamaServerUnavailable(Exception):
    """Raised when llama-server can't be reached after retries are exhausted."""


class LlamaServerError(Exception):
    """Raised when llama-server responds with an error status after retries."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"llama-server returned {status_code}: {detail}")


_RETRYABLE_STATUS_CODES = {502, 503, 504}


class LlamaClient:
    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 120.0,
        max_retries: int = 3,
        backoff_base_seconds: float = 0.5,
    ):
        self.base_url = base_url or settings.llama_server_base_url
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)
        self.max_retries = max_retries
        self.backoff_base_seconds = backoff_base_seconds

    async def _post_with_retry(self, path: str, payload: dict[str, Any]) -> httpx.Response:
        last_exc: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                resp = await self._client.post(path, json=payload)
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout) as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    await self._sleep_backoff(attempt)
                    continue
                raise LlamaServerUnavailable(
                    "Could not reach llama-server after retries"
                ) from exc

            if resp.status_code in _RETRYABLE_STATUS_CODES and attempt < self.max_retries:
                await self._sleep_backoff(attempt)
                continue

            if resp.status_code >= 400:
                raise LlamaServerError(resp.status_code, resp.text)

            return resp

        # Unreachable in practice, but keeps type checkers happy
        raise LlamaServerUnavailable(str(last_exc))

    async def _sleep_backoff(self, attempt: int) -> None:
        delay = self.backoff_base_seconds * (2**attempt)
        logger.warning("llama-server request failed, retrying in %.2fs", delay)
        await asyncio.sleep(delay)

    async def chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Non-streaming chat completion, proxied to llama-server with retries."""
        resp = await self._post_with_retry("/v1/chat/completions", payload)
        return resp.json()

    async def chat_completion_stream(
        self, payload: dict[str, Any]
    ) -> AsyncIterator[bytes]:
        """Streaming chat completion (SSE passthrough from llama-server).

        No retry here by design - once bytes start streaming to the caller,
        retrying would mean either duplicating already-sent content or
        silently truncating it. A connection failure before any bytes have
        been sent still raises cleanly.
        """
        try:
            async with self._client.stream(
                "POST", "/v1/chat/completions", json={**payload, "stream": True}
            ) as resp:
                if resp.status_code >= 400:
                    body = await resp.aread()
                    raise LlamaServerError(resp.status_code, body.decode(errors="replace"))
                async for chunk in resp.aiter_bytes():
                    yield chunk
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout) as exc:
            raise LlamaServerUnavailable("Could not reach llama-server") from exc

    async def health(self) -> bool:
        try:
            resp = await self._client.get("/health")
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    async def close(self) -> None:
        await self._client.aclose()


llama_client = LlamaClient()

