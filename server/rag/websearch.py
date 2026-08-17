"""Live web search retrieval.

This talks to a search API (Brave Search or Serper, your choice, configured
via .env) purely to fetch raw result snippets. It never calls another LLM's
API - the fetched snippets are just additional context handed to the local
Llama model, same as any other tool-use result.

If WEB_SEARCH_API_KEY / WEB_SEARCH_PROVIDER aren't set, this returns an
empty list rather than failing, so RAG still works with local documents
only.
"""

from __future__ import annotations

from typing import Any

import httpx

from server.core.config import settings

_BRAVE_URL = "https://api.search.brave.com/res/v1/web/search"
_SERPER_URL = "https://google.serper.dev/search"


async def web_search(query: str, top_k: int = 4) -> list[dict[str, Any]]:
    provider = settings.web_search_provider.lower().strip()
    api_key = settings.web_search_api_key

    if not provider or not api_key:
        return []

    async with httpx.AsyncClient(timeout=15.0) as client:
        if provider == "brave":
            resp = await client.get(
                _BRAVE_URL,
                params={"q": query, "count": top_k},
                headers={"X-Subscription-Token": api_key},
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("web", {}).get("results", [])
            return [
                {
                    "title": r.get("title", ""),
                    "snippet": r.get("description", ""),
                    "url": r.get("url", ""),
                }
                for r in results[:top_k]
            ]

        if provider == "serper":
            resp = await client.post(
                _SERPER_URL,
                json={"q": query, "num": top_k},
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("organic", [])
            return [
                {
                    "title": r.get("title", ""),
                    "snippet": r.get("snippet", ""),
                    "url": r.get("link", ""),
                }
                for r in results[:top_k]
            ]

        # Unknown provider configured - fail safe rather than erroring the request
        return []
