"""Tests for the request logging middleware and JSON log formatter."""

import json
import logging

from fastapi.testclient import TestClient

from server.core.logging_config import JsonFormatter
from server.main import app

client = TestClient(app)


def test_response_includes_request_id_header() -> None:
    resp = client.get("/api")
    assert "X-Request-ID" in resp.headers
    assert len(resp.headers["X-Request-ID"]) == 36  # UUID4 string length


def test_request_id_differs_per_request() -> None:
    id1 = client.get("/api").headers["X-Request-ID"]
    id2 = client.get("/api").headers["X-Request-ID"]
    assert id1 != id2


def test_access_log_emits_metadata_without_body_content(caplog) -> None:
    with caplog.at_level(logging.INFO, logger="anvilllm.access"):
        client.get("/api")

    records = [r for r in caplog.records if r.name == "anvilllm.access"]
    assert len(records) >= 1
    record = records[-1]

    assert record.method == "GET"
    assert record.path == "/api"
    assert record.status_code == 200
    assert hasattr(record, "duration_ms")
    assert hasattr(record, "client_id")
    # client_id should be a short hash, never the raw IP or API key
    assert len(record.client_id) == 12


def test_json_formatter_produces_valid_json_without_prompt_fields() -> None:
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="anvilllm.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request",
        args=(),
        exc_info=None,
    )
    record.method = "POST"
    record.path = "/v1/chat/completions"
    record.status_code = 200
    record.duration_ms = 42.1
    record.client_id = "abc123def456"

    output = json.loads(formatter.format(record))

    assert output["message"] == "request"
    assert output["method"] == "POST"
    assert output["status_code"] == 200
    # Confirms no accidental fields like "messages" or "content" leak in
    assert "messages" not in output
    assert "content" not in output
    assert "prompt" not in output
