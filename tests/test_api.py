"""Basic smoke tests for the AnvilLLM API layer.

These mock out the llama.cpp backend entirely so they run without needing
a real model or GPU/CPU inference - useful for CI (feat/ci-cd).
"""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


def test_root_serves_web_ui() -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "AnvilLLM" in resp.text


def test_api_info() -> None:
    resp = client.get("/api")
    assert resp.status_code == 200
    assert resp.json()["name"] == "AnvilLLM"


def test_list_models_no_auth_required_when_key_unset() -> None:
    resp = client.get("/v1/models")
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"][0]["id"] == "llama-3.1-8b-instruct"


@patch("server.core.llama_client.llama_client.health", new_callable=AsyncMock)
def test_healthz_reports_backend_status(mock_health: AsyncMock) -> None:
    mock_health.return_value = True
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "llama_server": True}


@patch("server.core.llama_client.llama_client.chat_completion", new_callable=AsyncMock)
def test_chat_completions_proxies_to_backend(mock_chat: AsyncMock) -> None:
    mock_chat.return_value = {
        "id": "chatcmpl-test",
        "choices": [{"message": {"role": "assistant", "content": "Hi there!"}}],
    }
    resp = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Hello"}]},
    )
    assert resp.status_code == 200
    assert resp.json()["choices"][0]["message"]["content"] == "Hi there!"
    mock_chat.assert_awaited_once()
