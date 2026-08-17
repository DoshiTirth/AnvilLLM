"""Thin async client for talking to the underlying llama.cpp server.

This is the only module that knows llama-server's address. Everything else
in the API talks to functions here, so swapping the inference backend later
(e.g. to vLLM) only touches this file.
"""

from collections.abc import AsyncIterator
from typing import Any

import httpx

from server.core.config import settings


class LlamaClient:
    def __init__(self, base_url: str | None = None, timeout: float = 120.0):
        self.base_url = base_url or settings.llama_server_base_url
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)

    async def chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Non-streaming chat completion, proxied straight to llama-server."""
        resp = await self._client.post("/v1/chat/completions", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def chat_completion_stream(
        self, payload: dict[str, Any]
    ) -> AsyncIterator[bytes]:
        """Streaming chat completion (SSE passthrough from llama-server)."""
        async with self._client.stream(
            "POST", "/v1/chat/completions", json={**payload, "stream": True}
        ) as resp:
            resp.raise_for_status()
            async for chunk in resp.aiter_bytes():
                yield chunk

    async def health(self) -> bool:
        try:
            resp = await self._client.get("/health")
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    async def close(self) -> None:
        await self._client.aclose()


llama_client = LlamaClient()
