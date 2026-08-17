"""
Router Node
───────────
Classifies how well internal retrieval answers the question.

Writes: state["routing"]  →  "sufficient" | "partial" | "insufficient"
"""
from __future__ import annotations

import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from config import settings


_llm = ChatOpenAI(
    model=settings.chat_model,
    api_key=settings.openai_api_key,
    temperature=0,
    max_tokens=8,
)

WEB_INTENT_RE = re.compile(
    r"("
    r"search the web|web\s*search|google it|google this|"
    r"from the internet|on the internet|look (it )?up online|"
    r"online sources?|external sources?|outside (the )?(kb|knowledge|docs)|"
    r"add web\s*search|use web search|browse the web|latest news|"
    r"also search (the )?(web|internet)|include web"
    r")",
    re.IGNORECASE,
)

SYSTEM_PROMPT = """You are a routing classifier for an enterprise RAG system.

You receive a user question and excerpts retrieved from an internal knowledge base.
Reply with EXACTLY one of these three words:

- sufficient     internal excerpts fully answer the question; web search is not needed
- partial        excerpts answer some of the question, or the user asked for web/internet/outside sources in addition to internal docs
- insufficient   excerpts do not answer the question (wrong topic, empty, or too thin)

Rules:
1. If the user asks to search the web, internet, Google, online, or outside knowledge, NEVER return sufficient. Use partial when internal excerpts still help, otherwise insufficient.
2. Multi-part questions where docs cover only some parts → partial.
3. Vague overlap or related-but-not-answering chunks → insufficient, not sufficient.
4. Do not be generous with sufficient. Only use it when a competent colleague could answer from the excerpts alone.

No explanation. One word only."""


def _wants_web(question: str) -> bool:
    return bool(WEB_INTENT_RE.search(question or ""))


def _truncate_chunks(chunks: list[dict], per_chunk: int = 350, max_chunks: int = 3) -> str:
    parts = []
    for c in chunks[:max_chunks]:
        text = (c.get("text") or "")[:per_chunk]
        parts.append(f"[{c.get('filename', '?')} | chunk {c.get('chunk_index', 0)}]\n{text}")
    return "\n\n".join(parts)


async def router_node(state: dict) -> dict:
    """LangGraph node: classify internal retrieval quality."""
    question: str = state["question"]
    chunks: list = state.get("internal_chunks", [])
    wants_web = _wants_web(question)

    if not chunks:
        return {"routing": "insufficient"}

    # Explicit web-search intent: never skip Tavily.
    if wants_web:
        return {"routing": "partial"}

    context = _truncate_chunks(chunks)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Question: {question}\n\nInternal excerpts:\n{context}"),
    ]

    response = await _llm.ainvoke(messages)
    raw = (response.content or "").strip().lower()
    # Take the first token in case the model adds extra words.
    routing = raw.split()[0] if raw else "partial"

    aliases = {
        "complete": "sufficient",
        "sufficient": "sufficient",
        "partial": "partial",
        "none": "insufficient",
        "insufficient": "insufficient",
    }
    routing = aliases.get(routing, "partial")

    return {"routing": routing}
