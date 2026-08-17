"""
Query Router
────────────
POST /query – Run the RAG LangGraph pipeline and return the blended answer.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from graph import run_query
from models import InternalResult, QueryRequest, QueryResponse, WebResult

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
    """
    if not body.question.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question must not be empty.",
        )

    result = await run_query(question=body.question, user_id=user_id)

    # Map raw graph routing to Pydantic model Literal
    graph_routing = result.get("routing", "none")
    routing_map = {
        "complete": "internal_only",
        "partial": "blended",
        "none": "web_only",
        "casual": "casual"
    }
    routing = routing_map.get(graph_routing, "web_only")

    internal = None
    if result.get("internal"):
        internal = InternalResult(**result["internal"])

    web = None
    if result.get("web"):
        web = WebResult(**result["web"])

    return QueryResponse(
        question=body.question,
        routing=routing,
        internal=internal,
        web=web,
        casual_answer=result.get("casual_answer")
    )
