"""
Web Search Agent Node
─────────────────────
Uses Tavily search to fetch web results when internal knowledge is insufficient.

Reads:  state["question"], state["routing"]
Writes: state["web_results"]  (list of dicts: {title, url, content})
"""
from __future__ import annotations

from tavily import AsyncTavilyClient

from config import settings


_tavily = AsyncTavilyClient(api_key=settings.tavily_api_key)


async def web_search_agent_node(state: dict) -> dict:
    """LangGraph node: run Tavily web search."""
    question: str = state["question"]
    routing: str = state.get("routing", "none")

    # Only run if routing demands it
    if routing in ("complete", "sufficient"):
        return {"web_results": []}

    response = await _tavily.search(
        query=question,
        search_depth="basic",
        max_results=3,
        include_answer=False,
    )

    results = [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
        }
        for r in response.get("results", [])
    ]

    return {"web_results": results}
