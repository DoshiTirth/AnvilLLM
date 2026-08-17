"""Local, self-hosted vector store for document retrieval.

Uses ChromaDB in persistent (on-disk) mode with its default local embedding
function - no external embedding API calls, everything stays on-device.
"""

from __future__ import annotations

import uuid
from typing import Any

import chromadb

from server.core.config import settings

_COLLECTION_NAME = "anvilllm_documents"


class VectorStore:
    def __init__(self, persist_path: str | None = None):
        self._client = chromadb.PersistentClient(
            path=persist_path or settings.vector_store_path
        )
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME
        )

    def add_documents(
        self, texts: list[str], metadatas: list[dict[str, Any]] | None = None
    ) -> list[str]:
        ids = [str(uuid.uuid4()) for _ in texts]
        self._collection.add(
            documents=texts,
            metadatas=metadatas or [{} for _ in texts],
            ids=ids,
        )
        return ids

    def query(self, query_text: str, top_k: int = 4) -> list[dict[str, Any]]:
        results = self._collection.query(query_texts=[query_text], n_results=top_k)
        hits: list[dict[str, Any]] = []
        docs = results.get("documents") or [[]]
        metas = results.get("metadatas") or [[]]
        dists = results.get("distances") or [[]]
        for doc, meta, dist in zip(docs[0], metas[0], dists[0], strict=False):
            hits.append({"text": doc, "metadata": meta, "distance": dist})
        return hits

    def count(self) -> int:
        return self._collection.count()


vector_store = VectorStore()
