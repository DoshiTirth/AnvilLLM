"""Tests for API key auth and rate limiting."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

import server.core.config as config_module
from server.main import app

client = TestClient(app)


@pytest.fixture
def with_api_keys():
    """Temporarily enable auth with two known keys."""
    original = config_module.settings.api_keys
    config_module.settings.api_keys = "test-key-1,test-key-2"
    yield
    config_module.settings.api_keys = original


def test_models_endpoint_requires_key_when_auth_enabled(with_api_keys) -> None:
    resp = client.get("/v1/models")
    assert resp.status_code == 401


def test_models_endpoint_rejects_wrong_key(with_api_keys) -> None:
    resp = client.get("/v1/models", headers={"Authorization": "Bearer wrong-key"})
    assert resp.status_code == 401


def test_models_endpoint_accepts_valid_key(with_api_keys) -> None:
    resp = client.get("/v1/models", headers={"Authorization": "Bearer test-key-1"})
    assert resp.status_code == 200


def test_models_endpoint_accepts_any_configured_key(with_api_keys) -> None:
    resp = client.get("/v1/models", headers={"Authorization": "Bearer test-key-2"})
    assert resp.status_code == 200


def test_api_key_list_parses_comma_separated() -> None:
    original = config_module.settings.api_keys
    config_module.settings.api_keys = " key-a , key-b ,, key-c "
    try:
        assert config_module.settings.api_key_list == ["key-a", "key-b", "key-c"]
    finally:
        config_module.settings.api_keys = original


@patch("server.core.llama_client.llama_client.chat_completion", new_callable=AsyncMock)
def test_rate_limit_returns_429_when_exceeded(mock_chat: AsyncMock) -> None:
    mock_chat.return_value = {
        "id": "chatcmpl-test",
        "choices": [{"message": {"role": "assistant", "content": "hi"}}],
    }
    original_limit = config_module.settings.rate_limit_per_minute
    config_module.settings.rate_limit_per_minute = 2
    try:
        payload = {"messages": [{"role": "user", "content": "hello"}]}
        statuses = [
            client.post("/v1/chat/completions", json=payload).status_code
            for _ in range(4)
        ]
        assert 429 in statuses
    finally:
        config_module.settings.rate_limit_per_minute = original_limit
