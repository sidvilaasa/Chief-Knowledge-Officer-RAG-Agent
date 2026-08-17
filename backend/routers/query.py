"""
Query Router
────────────
POST /query – Run the RAG LangGraph pipeline and return the blended answer.
             Session management is handled automatically:
               • If session_id is omitted, a new session is created.
               • A rolling conversation summary (≤1024 tokens) is injected.
               • The Q&A pair, citations, and agent name are persisted.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from graph import run_query
from history import compact_history
from models import InternalResult, QueryRequest, QueryResponse, WebResult
from session_manager import (
    add_messages,
    get_or_create_session,
    set_session_summary,
    set_session_title,
    touch_session,
)

router = APIRouter(prefix="/query", tags=["Query"])

ROUTING_MAP = {
    "sufficient": "internal_only",
    "complete": "internal_only",
    "partial": "blended",
    "insufficient": "web_only",
    "none": "web_only",
    "casual": "casual",
}

AGENT_NAMES = {
    "internal_only": "Knowledge Agent",
    "web_only": "Web Search Agent",
    "blended": "Knowledge + Web Agent",
    "casual": "Casual Agent",
}


@router.post("", response_model=QueryResponse)
async def query(
    body: QueryRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Run the Chief-knowledge-officer RAG pipeline.

    The graph will:
    1. Search the user's accessible documents (own + global)
    2. Route based on answer completeness (sufficient / partial / insufficient)
    3. Optionally supplement with web search
    4. Return a structured response with citations and the agent name
    """
    if not body.question.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question must not be empty.",
        )

    session = await get_or_create_session(user_id, body.session_id)
    session_id: str = session["id"]
    session_title: str | None = session.get("title")
    history_summary: str = session.get("conversation_summary") or ""

    await touch_session(session_id)

    result = await run_query(
        question=body.question,
        user_id=user_id,
        chat_history_summary=history_summary,
    )

    graph_routing = result.get("routing", "insufficient")
    routing = ROUTING_MAP.get(graph_routing, "web_only")
    agent_name = result.get("agent_name") or AGENT_NAMES.get(routing, "Knowledge Agent")

    internal = None
    if result.get("internal"):
        internal = InternalResult(**result["internal"])

    web = None
    if result.get("web"):
        web = WebResult(**result["web"])

    citations: list[str] = []
    if internal:
        citations.extend(internal.citations or [])
    if web:
        citations.extend(web.citations or [])
    # Preserve order, drop duplicates
    citations = list(dict.fromkeys(citations))

    if result.get("casual_answer"):
        answer_text = result["casual_answer"]
    elif internal and internal.answer:
        answer_text = internal.answer
        if web and web.answer:
            answer_text = f"{internal.answer}\n\n{web.answer}"
    elif web:
        answer_text = web.answer
    else:
        answer_text = ""

    await add_messages(
        session_id,
        body.question,
        answer_text,
        citations=citations,
        agent_name=agent_name,
    )
    if not session_title:
        await set_session_title(session_id, body.question)
        session_title = body.question[:200]

    new_summary = compact_history(history_summary, body.question, answer_text)
    await set_session_summary(session_id, new_summary)

    return QueryResponse(
        question=body.question,
        session_id=session_id,
        session_title=session_title,
        routing=routing,
        agent_name=agent_name,
        internal=internal,
        web=web,
        casual_answer=result.get("casual_answer"),
    )
