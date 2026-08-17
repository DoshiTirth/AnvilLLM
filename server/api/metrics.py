"""Prometheus-compatible metrics.

Tracks request counts (by method, path, status) and request latency. No
request/response content is ever recorded here - metrics are numeric
aggregates only, same privacy posture as the request logging middleware.
"""

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_COUNT = Counter(
    "anvilllm_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "anvilllm_request_duration_seconds",
    "Request duration in seconds",
    ["method", "path"],
)

LLAMA_SERVER_ERRORS = Counter(
    "anvilllm_llama_server_errors_total",
    "Total errors from the llama-server backend",
    ["error_type"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Use the route's path template (e.g. "/v1/chat/completions"), not
        # the raw URL, so metrics don't get an unbounded label cardinality
        # from path parameters or query strings.
        path = request.url.path

        with REQUEST_LATENCY.labels(method=request.method, path=path).time():
            response = await call_next(request)

        REQUEST_COUNT.labels(
            method=request.method, path=path, status_code=response.status_code
        ).inc()

        return response


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
