"""
Blender Node
────────────
Final synthesis — one LLM call, with citations and a rolling history summary.
"""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from config import settings

AGENT_NAMES = {
    "sufficient": "Knowledge Agent",
    "partial": "Knowledge + Web Agent",
    "insufficient": "Web Search Agent",
    "complete": "Knowledge Agent",
    "none": "Web Search Agent",
}

_llm = ChatOpenAI(
    model=settings.chat_model,
    api_key=settings.openai_api_key,
    temperature=0.2,
    max_tokens=700,
)

SYSTEM = "You are a professional enterprise knowledge assistant. Be concise and accurate."


def _format_internal(chunks: list[dict]) -> str:
    return "\n\n".join(
        f"[{c['filename']} | chunk {c['chunk_index']}]\n{c['text']}"
        for c in chunks
    )


def _format_web(results: list[dict]) -> str:
    return "\n\n".join(
        f"[{r['title']} | {r['url']}]\n{r['content']}"
        for r in results
    )


def _extract_citations_internal(chunks: list[dict]) -> list[str]:
    return list(dict.fromkeys(c["filename"] for c in chunks))


def _extract_citations_web(results: list[dict]) -> list[str]:
    return [r["url"] for r in results if r.get("url")]


def _history_block(summary: str) -> str:
    summary = (summary or "").strip()
    if not summary:
        return ""
    return f"Conversation so far (summary, ≤1024 tokens):\n{summary}\n\n"


async def blender_node(state: dict) -> dict:
    question: str = state["question"]
    routing: str = state.get("routing", "insufficient")
    chunks: list = state.get("internal_chunks", [])
    web_results: list = state.get("web_results", [])
    history = _history_block(state.get("chat_history_summary") or "")

    final: dict = {
        "question": question,
        "routing": routing,
        "agent_name": AGENT_NAMES.get(routing, "Knowledge Agent"),
    }

    if routing in ("sufficient", "complete"):
        prompt = (
            f"{history}"
            "Answer the question using ONLY the internal document excerpts. "
            "Use prior conversation only for context.\n\n"
            f"Question: {question}\n\nInternal Documents:\n{_format_internal(chunks)}"
        )
        resp = await _llm.ainvoke(
            [SystemMessage(content=SYSTEM), HumanMessage(content=prompt)]
        )
        final["internal"] = {
            "answer": resp.content,
            "citations": _extract_citations_internal(chunks),
        }
        final["web"] = None
        return {"final_answer": final}

    if routing in ("insufficient", "none") or not chunks:
        prompt = (
            f"{history}"
            "Answer the question using ONLY the web search results. "
            "Use prior conversation only for context.\n\n"
            f"Question: {question}\n\nWeb Results:\n{_format_web(web_results)}"
        )
        resp = await _llm.ainvoke(
            [SystemMessage(content=SYSTEM), HumanMessage(content=prompt)]
        )
        final["internal"] = None
        final["web"] = {
            "answer": resp.content,
            "citations": _extract_citations_web(web_results),
        }
        final["agent_name"] = AGENT_NAMES["insufficient"]
        return {"final_answer": final}

    # partial — single synthesis call (previously two sequential LLM calls)
    prompt = (
        f"{history}"
        "Write one coherent answer in two labeled sections:\n"
        "1) Internal knowledge — what the document excerpts confirm.\n"
        "2) Web supplement — what the web results add that internal docs did not cover.\n"
        "Do not invent sources.\n\n"
        f"Question: {question}\n\n"
        f"Internal Documents:\n{_format_internal(chunks)}\n\n"
        f"Web Results:\n{_format_web(web_results)}"
    )
    resp = await _llm.ainvoke(
        [SystemMessage(content=SYSTEM), HumanMessage(content=prompt)]
    )
    answer = resp.content
    final["internal"] = {
        "answer": answer,
        "citations": _extract_citations_internal(chunks),
    }
    final["web"] = {
        "answer": "",
        "citations": _extract_citations_web(web_results),
    }
    return {"final_answer": final}
