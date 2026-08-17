"""Logging setup.

Deliberately does NOT log request/response bodies (prompts, completions,
ingested document text) anywhere by default - only request metadata
(method, path, status, duration, caller identity, request id). This keeps
log files from becoming an unintended store of sensitive conversation
content.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any

from server.core.config import settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Anything passed via `extra={...}` gets merged in, e.g. request_id,
        # method, path, status_code, duration_ms, client_id.
        for key, value in record.__dict__.items():
            if key in _STANDARD_LOG_RECORD_KEYS:
                continue
            payload[key] = value
        return json.dumps(payload, default=str)


_STANDARD_LOG_RECORD_KEYS = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "taskName",
}


def setup_logging() -> None:
    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())

    # Avoid duplicate handlers on reload
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if settings.log_json:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
    root.addHandler(handler)


def now_ms() -> float:
    return time.perf_counter() * 1000
