"""Per-request logging middleware.

Logs method, path, status code, duration, and a caller identity derived the
same way rate limiting keys requests (API key if present, else source IP -
never the raw key or IP is logged verbatim; both are hashed to keep logs
useful for correlation without being a credential/PII store themselves).

Never logs request or response bodies.
"""

from __future__ import annotations

import hashlib
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("anvilllm.access")


def _hash_identity(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:12]


def _client_identity(request: Request) -> str:
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        return _hash_identity(auth.removeprefix("Bearer ").strip())
    client = request.client.host if request.client else "unknown"
    return _hash_identity(client)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client_id": _client_identity(request),
            },
        )

        return response
