"""
Query Router
────────────
POST /query – Run the RAG LangGraph pipeline and return the blended answer.
             Session management is handled automatically:
               • If session_id is omitted, a new session is created.
               • Chat history (last 10 messages) is injected into the graph.
               • The Q&A pair is persisted and the session's last_used_at is updated.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from graph import run_query
from models import InternalResult, QueryRequest, QueryResponse, WebResult
from session_manager import (
    add_messages,
    get_history,
    get_or_create_session,
    set_session_title,
    touch_session,
)

router = APIRouter(prefix="/query", tags=["Query"])


@router.post("", response_model=QueryResponse)
async def query(
    body: QueryRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Run the Chief-of-Staff RAG pipeline.

    The graph will:
    1. Search the user's accessible documents (own + global)
    2. Route based on answer completeness
    3. Optionally supplement with web search
    4. Return a structured response with citations

    Session behaviour:
    - Pass ``session_id`` to continue an existing conversation.
    - Omit it to auto-create a new session (returned in the response).
    - The last 10 messages of the session are injected as context.
    """
    if not body.question.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question must not be empty.",
        )

    # ── Session lifecycle ─────────────────────────────────────────────────────
    session = await get_or_create_session(user_id, body.session_id)
    session_id: str = session["id"]
    session_title: str | None = session.get("title")

    await touch_session(session_id)
    chat_history = await get_history(session_id)

    # ── RAG pipeline ──────────────────────────────────────────────────────────
    result = await run_query(
        question=body.question,
        user_id=user_id,
        chat_history=chat_history,
    )

    # ── Map routing label ─────────────────────────────────────────────────────
    graph_routing = result.get("routing", "none")
    routing_map = {
        "complete": "internal_only",
        "partial":  "blended",
        "none":     "web_only",
        "casual":   "casual",
    }
    routing = routing_map.get(graph_routing, "web_only")

    internal = None
    if result.get("internal"):
        internal = InternalResult(**result["internal"])

    web = None
    if result.get("web"):
        web = WebResult(**result["web"])

    # Build a plain-text answer for storage
    if result.get("casual_answer"):
        answer_text = result["casual_answer"]
    elif internal:
        answer_text = internal.answer
    elif web:
        answer_text = web.answer
    else:
        answer_text = ""

    # ── Persist messages + auto-set title on first turn ───────────────────────
    await add_messages(session_id, body.question, answer_text)
    if not session_title:
        await set_session_title(session_id, body.question)
        session_title = body.question[:200]

    return QueryResponse(
        question=body.question,
        session_id=session_id,
        session_title=session_title,
        routing=routing,
        internal=internal,
        web=web,
        casual_answer=result.get("casual_answer"),
    )

