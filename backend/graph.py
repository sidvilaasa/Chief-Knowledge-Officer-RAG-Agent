"""
LangGraph StateGraph
────────────────────
Wires together all agent nodes with conditional routing:

  orchestrator → knowledge_agent → router → [web_search] → blender → END

Routing map:
  "sufficient"    → skip web search, go straight to blender
  "partial"       → run web search, then blender
  "insufficient"  → run web search, then blender
"""
from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, StateGraph

from agents.blender_node import blender_node
from agents.casual_node import casual_node
from agents.knowledge_agent import knowledge_agent_node
from agents.orchestrator_node import orchestrator_node
from agents.router_node import router_node
from agents.web_search_agent import web_search_agent_node


class AgentState(TypedDict, total=False):
    question: str
    user_id: str
    chat_history_summary: str

    orchestration: str  # "casual" | "rag"
    internal_chunks: list[dict]
    routing: str  # "sufficient" | "partial" | "insufficient"
    web_results: list[dict]

    final_answer: dict


def _route_after_orchestrator(state: AgentState) -> str:
    if state.get("orchestration", "rag") == "casual":
        return "casual"
    return "knowledge_agent"


def _route_after_router(state: AgentState) -> str:
    routing = state.get("routing", "insufficient")
    if routing in ("sufficient", "complete"):
        return "blender"
    return "web_search"


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("casual", casual_node)
    graph.add_node("knowledge_agent", knowledge_agent_node)
    graph.add_node("router", router_node)
    graph.add_node("web_search", web_search_agent_node)
    graph.add_node("blender", blender_node)

    graph.set_entry_point("orchestrator")

    graph.add_conditional_edges(
        "orchestrator",
        _route_after_orchestrator,
        {
            "casual": "casual",
            "knowledge_agent": "knowledge_agent",
        },
    )

    graph.add_edge("casual", END)
    graph.add_edge("knowledge_agent", "router")

    graph.add_conditional_edges(
        "router",
        _route_after_router,
        {
            "blender": "blender",
            "web_search": "web_search",
        },
    )

    graph.add_edge("web_search", "blender")
    graph.add_edge("blender", END)

    return graph


compiled_graph = build_graph().compile()


async def run_query(
    question: str,
    user_id: str,
    chat_history_summary: str | None = None,
) -> dict:
    """Entry point called by the API router."""
    result = await compiled_graph.ainvoke(
        {
            "question": question,
            "user_id": user_id,
            "chat_history_summary": chat_history_summary or "",
        }
    )
    return result.get("final_answer", {})
