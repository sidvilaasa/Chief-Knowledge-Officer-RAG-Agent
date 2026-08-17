"""
Blender Node
────────────
Final synthesis — produces a structured two-section answer with citations.

Reads:  state["question"], state["routing"],
        state["internal_chunks"], state["web_results"]
Writes: state["final_answer"]  (dict matching QueryResponse shape)
"""
from __future__ import annotations

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from config import settings


_llm = ChatOpenAI(
    api_key=settings.openai_api_key,
    temperature=0.2,
    max_tokens=1024,
)

INTERNAL_ONLY_PROMPT = """You are an enterprise knowledge assistant.
Answer the question using ONLY the provided internal document excerpts.
Be concise, accurate, and professional.

At the end, list the exact source references used as citations
in the format:  • <filename>

Question: {question}

Internal Documents:
{context}"""

WEB_ONLY_PROMPT = """You are an enterprise knowledge assistant.
Answer the question using ONLY the provided web search results.
Be concise, accurate, and professional.

At the end, list source URLs as citations:  • <url>

Question: {question}

Web Results:
{context}"""

BLEND_INTERNAL_PROMPT = """You are an enterprise knowledge assistant.
Write a partial answer using ONLY the provided internal document excerpts.
Focus on what the internal docs can confirm.
List source citations at the end:  • <filename>

Question: {question}

Internal Documents:
{context}"""

BLEND_WEB_PROMPT = """You are an enterprise knowledge assistant.
Write a supplemental answer using ONLY the provided web search results,
covering what the internal docs did NOT fully answer.
List source URLs at the end:  • <url>

Question: {question}

Web Results:
{context}"""


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
    # Deduplicate citations to only show unique document filenames
    return list(dict.fromkeys(c["filename"] for c in chunks))


def _extract_citations_web(results: list[dict]) -> list[str]:
    return [r["url"] for r in results if r.get("url")]


async def blender_node(state: dict) -> dict:
    """LangGraph node: produce final answer."""
    question: str = state["question"]
    routing: str = state.get("routing", "none")
    chunks: list = state.get("internal_chunks", [])
    web_results: list = state.get("web_results", [])

    final: dict = {"question": question, "routing": routing}

    if routing == "complete":
        # Internal only
        context = _format_internal(chunks)
        resp = await _llm.ainvoke(
            [
                SystemMessage(content="You are a professional knowledge assistant."),
                HumanMessage(
                    content=INTERNAL_ONLY_PROMPT.format(
                        question=question, context=context
                    )
                ),
            ]
        )
        final["internal"] = {
            "answer": resp.content,
            "citations": _extract_citations_internal(chunks),
        }
        final["web"] = None

    elif routing == "none":
        # Web only
        context = _format_web(web_results)
        resp = await _llm.ainvoke(
            [
                SystemMessage(content="You are a professional knowledge assistant."),
                HumanMessage(
                    content=WEB_ONLY_PROMPT.format(
                        question=question, context=context
                    )
                ),
            ]
        )
        final["internal"] = None
        final["web"] = {
            "answer": resp.content,
            "citations": _extract_citations_web(web_results),
        }

    else:
        # Blended (partial)
        int_context = _format_internal(chunks)
        int_resp = await _llm.ainvoke(
            [
                SystemMessage(content="You are a professional knowledge assistant."),
                HumanMessage(
                    content=BLEND_INTERNAL_PROMPT.format(
                        question=question, context=int_context
                    )
                ),
            ]
        )

        web_context = _format_web(web_results)
        web_resp = await _llm.ainvoke(
            [
                SystemMessage(content="You are a professional knowledge assistant."),
                HumanMessage(
                    content=BLEND_WEB_PROMPT.format(
                        question=question, context=web_context
                    )
                ),
            ]
        )

        final["internal"] = {
            "answer": int_resp.content,
            "citations": _extract_citations_internal(chunks),
        }
        final["web"] = {
            "answer": web_resp.content,
            "citations": _extract_citations_web(web_results),
        }

    return {"final_answer": final}
