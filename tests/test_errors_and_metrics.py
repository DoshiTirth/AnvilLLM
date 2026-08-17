"""Tests for exception handler translation (via the live app) and /metrics."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from server.core.llama_client import LlamaServerError, LlamaServerUnavailable
from server.main import app

client = TestClient(app)


@patch("server.core.llama_client.llama_client.chat_completion", new_callable=AsyncMock)
def test_llama_unavailable_returns_503_with_openai_style_error(mock_chat) -> None:
    mock_chat.side_effect = LlamaServerUnavailable("could not connect")
    resp = client.post(
        "/v1/chat/completions", json={"messages": [{"role": "user", "content": "hi"}]}
    )
    assert resp.status_code == 503
    body = resp.json()
    assert body["error"]["type"] == "server_unavailable_error"


@patch("server.core.llama_client.llama_client.chat_completion", new_callable=AsyncMock)
def test_llama_upstream_5xx_returns_502(mock_chat) -> None:
    mock_chat.side_effect = LlamaServerError(500, "internal error")
    resp = client.post(
        "/v1/chat/completions", json={"messages": [{"role": "user", "content": "hi"}]}
    )
    assert resp.status_code == 502
    assert resp.json()["error"]["type"] == "server_error"


@patch("server.core.llama_client.llama_client.chat_completion", new_callable=AsyncMock)
def test_llama_upstream_4xx_passed_through(mock_chat) -> None:
    mock_chat.side_effect = LlamaServerError(400, "bad request shape")
    resp = client.post(
        "/v1/chat/completions", json={"messages": [{"role": "user", "content": "hi"}]}
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["type"] == "invalid_request_error"


def test_metrics_endpoint_returns_prometheus_format() -> None:
    # Generate at least one request so counters are non-empty
    client.get("/api")
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "anvilllm_requests_total" in resp.text
    assert "anvilllm_request_duration_seconds" in resp.text


def test_metrics_never_contains_request_body_content() -> None:
    client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "super-secret-prompt-xyz"}]},
    )
    resp = client.get("/metrics")
    assert "super-secret-prompt-xyz" not in resp.text
