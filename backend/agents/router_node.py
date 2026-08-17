"""
Router Node
───────────
LLM-based classifier that decides whether to use web search.

Reads:  state["question"], state["internal_chunks"]
Writes: state["routing"]  →  "complete" | "partial" | "none"
"""
from __future__ import annotations

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from config import settings


_llm = ChatOpenAI(
    model=settings.chat_model,
    api_key=settings.openai_api_key,
    temperature=0,
)

SYSTEM_PROMPT = """You are a routing assistant. 
Given a user question and context chunks retrieved from an internal knowledge base, 
decide how well the question is answered.

Reply with EXACTLY one word:
- "complete"  – the context fully answers the question
- "partial"   – the context partially answers the question and web search would help
- "none"      – the context does not address the question at all

No explanation, no punctuation — just the single word."""


async def router_node(state: dict) -> dict:
    """LangGraph node: classify internal retrieval quality."""
    question: str = state["question"]
    chunks: list = state.get("internal_chunks", [])

    if not chunks:
        return {"routing": "none"}

    context = "\n\n".join(
        f"[{c['filename']} | chunk {c['chunk_index']}]\n{c['text']}" for c in chunks
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"Question: {question}\n\nContext:\n{context}"
        ),
    ]

    response = await _llm.ainvoke(messages)
    routing = response.content.strip().lower()

    if routing not in ("complete", "partial", "none"):
        routing = "partial"  # safe fallback

    return {"routing": routing}
