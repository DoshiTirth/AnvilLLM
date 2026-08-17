"""Global exception handlers.

Translates internal exceptions into the OpenAI-style error JSON shape used
elsewhere in the API, and makes sure unexpected errors never leak a raw
stack trace to the client - full details go to the logs instead.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from server.core.llama_client import LlamaServerError, LlamaServerUnavailable

logger = logging.getLogger("anvilllm.errors")


def _error_response(status_code: int, message: str, error_type: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"message": message, "type": error_type}},
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(LlamaServerUnavailable)
    async def llama_unavailable_handler(request: Request, exc: LlamaServerUnavailable):
        from server.api.metrics import LLAMA_SERVER_ERRORS

        LLAMA_SERVER_ERRORS.labels(error_type="unavailable").inc()
        logger.error("llama-server unavailable: %s", exc)
        return _error_response(
            503,
            "The inference server is currently unreachable. Please try again shortly.",
            "server_unavailable_error",
        )

    @app.exception_handler(LlamaServerError)
    async def llama_error_handler(request: Request, exc: LlamaServerError):
        from server.api.metrics import LLAMA_SERVER_ERRORS

        LLAMA_SERVER_ERRORS.labels(error_type=str(exc.status_code)).inc()
        logger.error("llama-server error %s: %s", exc.status_code, exc.detail)
        # Pass through 4xx (bad request shape) as-is; treat upstream 5xx as
        # a 502 from our side, since it's our upstream that failed.
        if 400 <= exc.status_code < 500:
            return _error_response(exc.status_code, exc.detail, "invalid_request_error")
        return _error_response(
            502,
            "The inference server returned an error.",
            "server_error",
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return _error_response(
            500,
            "An unexpected error occurred.",
            "internal_error",
        )
