"""Tests for LlamaClient's retry-with-backoff and error translation."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from server.core.llama_client import (
    LlamaClient,
    LlamaServerError,
    LlamaServerUnavailable,
)


@pytest.fixture
def client() -> LlamaClient:
    return LlamaClient(base_url="http://fake-llama:8081", max_retries=2, backoff_base_seconds=0.01)


async def test_chat_completion_retries_on_connection_error_then_succeeds(client):
    success_response = httpx.Response(200, json={"id": "ok"})

    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise httpx.ConnectError("connection refused")
        return success_response

    with patch.object(client._client, "post", new=AsyncMock(side_effect=side_effect)):
        result = await client.chat_completion({"messages": []})

    assert result == {"id": "ok"}
    assert call_count == 3  # 2 failures + 1 success, within max_retries=2


async def test_chat_completion_raises_unavailable_after_exhausting_retries(client):
    async def always_fails(*args, **kwargs):
        raise httpx.ConnectError("connection refused")

    with patch.object(client._client, "post", new=AsyncMock(side_effect=always_fails)):
        with pytest.raises(LlamaServerUnavailable):
            await client.chat_completion({"messages": []})


async def test_chat_completion_retries_on_upstream_503_then_succeeds(client):
    responses = [
        httpx.Response(503, text="temporarily overloaded"),
        httpx.Response(200, json={"id": "ok"}),
    ]

    async def side_effect(*args, **kwargs):
        return responses.pop(0)

    with patch.object(client._client, "post", new=AsyncMock(side_effect=side_effect)):
        result = await client.chat_completion({"messages": []})

    assert result == {"id": "ok"}


async def test_chat_completion_raises_llama_server_error_on_persistent_4xx(client):
    async def side_effect(*args, **kwargs):
        return httpx.Response(400, text="bad request")

    with patch.object(client._client, "post", new=AsyncMock(side_effect=side_effect)):
        with pytest.raises(LlamaServerError) as exc_info:
            await client.chat_completion({"messages": []})

    assert exc_info.value.status_code == 400


async def test_chat_completion_does_not_retry_4xx(client):
    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return httpx.Response(400, text="bad request")

    with patch.object(client._client, "post", new=AsyncMock(side_effect=side_effect)):
        with pytest.raises(LlamaServerError):
            await client.chat_completion({"messages": []})

    assert call_count == 1  # no retries for non-retryable 4xx
