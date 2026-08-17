"""Combines local document retrieval and (optional) live web search into a
single context block to inject into the prompt before it reaches Llama.

This is the only place that decides *what* context to add - the chat
endpoint just asks for context and injects it, it doesn't know or care
where it came from.
"""

from __future__ import annotations

from server.rag.vectorstore import vector_store
from server.rag.websearch import web_search


async def build_context(query: str, top_k: int = 4) -> str:
    sections: list[str] = []

    try:
        doc_hits = vector_store.query(query, top_k=top_k)
    except Exception:
        doc_hits = []

    if doc_hits:
        doc_lines = "\n".join(f"- {hit['text']}" for hit in doc_hits)
        sections.append(f"Relevant local documents:\n{doc_lines}")

    web_hits = await web_search(query, top_k=top_k)
    if web_hits:
        web_lines = "\n".join(
            f"- {hit['title']}: {hit['snippet']} ({hit['url']})" for hit in web_hits
        )
        sections.append(f"Relevant web search results:\n{web_lines}")

    if not sections:
        return ""

    return (
        "The following context was retrieved to help answer the user's "
        "question. Use it if relevant, and ignore it if not:\n\n"
        + "\n\n".join(sections)
    )
