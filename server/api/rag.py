"""Endpoints for managing and testing the RAG layer."""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from server.api.auth import require_api_key
from server.api.rate_limit import limiter
from server.core.config import settings
from server.rag.chunking import chunk_text
from server.rag.retrieval import build_context
from server.rag.vectorstore import vector_store

router = APIRouter(prefix="/v1/rag", tags=["rag"])


class IngestRequest(BaseModel):
    text: str
    source: str = "manual"


class IngestResponse(BaseModel):
    chunks_added: int
    total_documents: int


class SearchRequest(BaseModel):
    query: str
    top_k: int = 4


@router.post("/ingest", response_model=IngestResponse, dependencies=[Depends(require_api_key)])
@limiter.limit("20/minute")
async def ingest_document(request: Request, body: IngestRequest) -> IngestResponse:
    chunks = chunk_text(body.text)
    if chunks:
        vector_store.add_documents(
            chunks, metadatas=[{"source": body.source} for _ in chunks]
        )
    return IngestResponse(chunks_added=len(chunks), total_documents=vector_store.count())


@router.post("/search", dependencies=[Depends(require_api_key)])
async def search_context(request: SearchRequest) -> dict:
    context = await build_context(request.query, top_k=request.top_k)
    return {"context": context, "rag_enabled": settings.enable_rag}

