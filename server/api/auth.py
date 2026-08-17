"""Optional API key authentication.

If settings.api_key is empty, auth is disabled entirely (local dev default).
If set, requests must include `Authorization: Bearer <key>`.
"""

from fastapi import Header, HTTPException, status

from server.core.config import settings


async def require_api_key(authorization: str | None = Header(default=None)) -> None:
    if not settings.api_key:
        return  # auth disabled

    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header",
        )

    token = authorization.removeprefix("Bearer ").strip()
    if token != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
