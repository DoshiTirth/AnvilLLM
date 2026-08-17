"""Model listing, health, and system status endpoints."""

import time

from fastapi import APIRouter, Depends

from server.api.auth import require_api_key
from server.core.config import settings
from server.core.llama_client import llama_client

router = APIRouter()

_START_TIME = time.time()


@router.get("/v1/models", dependencies=[Depends(require_api_key)])
async def list_models() -> dict:
    return {
        "object": "list",
        "data": [
            {
                "id": "llama-3.1-8b-instruct",
                "object": "model",
                "owned_by": "meta-llama",
                "context_length": settings.context_size,
            }
        ],
    }


@router.get("/healthz")
async def healthz() -> dict:
    backend_ok = await llama_client.health()
    return {"status": "ok" if backend_ok else "degraded", "llama_server": backend_ok}


@router.get("/v1/system", dependencies=[Depends(require_api_key)])
async def system_status() -> dict:
    return {
        "uptime_seconds": round(time.time() - _START_TIME, 1),
        "rag_enabled": settings.enable_rag,
        "context_size": settings.context_size,
    }
