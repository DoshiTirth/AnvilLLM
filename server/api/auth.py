"""API key authentication.

If settings.api_keys is empty, auth is disabled entirely (local dev
default). If set (comma-separated list), requests must include
`Authorization: Bearer <key>` matching one of the configured keys.

Comparison is constant-time (hmac.compare_digest) to avoid leaking timing
information about how much of a guessed key matched.
"""

import hmac

from fastapi import Header, HTTPException, status

from server.core.config import settings


def _matches_any(token: str, valid_keys: list[str]) -> bool:
    # Compare against every key (not short-circuiting on first match) so
    # response timing doesn't reveal which key index a partial match hit.
    return any(hmac.compare_digest(token, key) for key in valid_keys)


async def require_api_key(authorization: str | None = Header(default=None)) -> str:
    """Returns an identity string for the caller: the API key itself when
    auth is enabled (used to key per-client rate limits), or a fixed
    'anonymous' identity when auth is disabled.
    """
    valid_keys = settings.api_key_list

    if not valid_keys:
        return "anonymous"  # auth disabled

    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header",
        )

    token = authorization.removeprefix("Bearer ").strip()
    if not _matches_any(token, valid_keys):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return token
