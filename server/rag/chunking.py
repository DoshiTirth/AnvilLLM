"""Simple fixed-size text chunking for ingestion into the vector store.

Deliberately simple (no external NLP deps) - splits on whitespace-approximate
chunks with overlap. Good enough for a first pass; swap for a smarter
splitter later if needed.
"""

from __future__ import annotations


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")

    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    step = chunk_size - overlap
    approx_words_per_chunk = max(chunk_size // 6, 1)  # rough chars-per-word heuristic
    approx_step_words = max(step // 6, 1)

    i = 0
    while i < len(words):
        chunk_words = words[i : i + approx_words_per_chunk]
        if not chunk_words:
            break
        chunks.append(" ".join(chunk_words))
        i += approx_step_words

    return chunks
