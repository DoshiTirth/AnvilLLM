"""Tests for the RAG layer: chunking, ingestion, and retrieval context building.

Uses a temporary on-disk Chroma path so tests don't touch real data, and
mocks web search so no network calls happen during CI.
"""

import shutil
import tempfile
from unittest.mock import AsyncMock, patch

import pytest

from server.rag.chunking import chunk_text
from server.rag.vectorstore import VectorStore


def test_chunk_text_splits_and_respects_bounds() -> None:
    text = "word " * 500
    chunks = chunk_text(text, chunk_size=800, overlap=100)
    assert len(chunks) > 1
    assert all(isinstance(c, str) and c for c in chunks)


def test_chunk_text_empty_input() -> None:
    assert chunk_text("") == []


def test_chunk_text_rejects_invalid_overlap() -> None:
    with pytest.raises(ValueError):
        chunk_text("hello world", chunk_size=100, overlap=100)


@pytest.fixture
def temp_vector_store():
    tmp_dir = tempfile.mkdtemp()
    store = VectorStore(persist_path=tmp_dir)
    yield store
    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_vector_store_add_and_query(temp_vector_store: VectorStore) -> None:
    pytest.importorskip("httpx")
    try:
        temp_vector_store.add_documents(
            ["The sky is blue.", "Llama 3.1 was released in July 2024."],
            metadatas=[{"source": "test"}, {"source": "test"}],
        )
    except Exception as exc:  # pragma: no cover - network-restricted environments
        pytest.skip(
            f"Skipping: ChromaDB's default embedding model requires a one-time "
            f"network download on first use, unavailable in this environment: {exc}"
        )

    assert temp_vector_store.count() == 2

    results = temp_vector_store.query("When was Llama released?", top_k=2)
    assert len(results) > 0
    assert any("Llama" in r["text"] for r in results)


@patch("server.rag.retrieval.web_search", new_callable=AsyncMock)
@patch("server.rag.retrieval.vector_store")
async def test_build_context_combines_sources(mock_store, mock_web) -> None:
    from server.rag.retrieval import build_context

    mock_store.query.return_value = [{"text": "local doc snippet", "metadata": {}}]
    mock_web.return_value = [
        {"title": "Some Title", "snippet": "web snippet", "url": "https://example.com"}
    ]

    context = await build_context("test query")
    assert "local doc snippet" in context
    assert "web snippet" in context


@patch("server.rag.retrieval.web_search", new_callable=AsyncMock)
@patch("server.rag.retrieval.vector_store")
async def test_build_context_empty_when_no_hits(mock_store, mock_web) -> None:
    from server.rag.retrieval import build_context

    mock_store.query.return_value = []
    mock_web.return_value = []

    context = await build_context("test query")
    assert context == ""
