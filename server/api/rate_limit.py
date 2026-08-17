"""Rate limiting, keyed per API key (or per IP when auth is disabled).

Uses slowapi (an in-memory limiter) - fine for a single self-hosted
instance. If AnvilLLM is ever run as multiple replicas behind a load
balancer, this would need a shared backend (e.g. Redis) instead, since
in-memory limits don't sync across processes.
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from server.core.config import settings


def _rate_limit_key(request: Request) -> str:
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.removeprefix("Bearer ").strip()
    return get_remote_address(request)


limiter = Limiter(key_func=_rate_limit_key)


def rate_limit_string() -> str:
    return f"{settings.rate_limit_per_minute}/minute"
