"""
Casual Talk Node
─────────────────
Responds to casual chit-chat directly, using the rolling conversation summary.
"""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from config import settings

_llm = ChatOpenAI(
    model=settings.chat_model,
    api_key=settings.openai_api_key,
    temperature=0.6,
    max_tokens=220,
)


async def casual_node(state: dict) -> dict:
    question = state["question"]
    summary = (state.get("chat_history_summary") or "").strip()
    history = (
        f"Conversation so far:\n{summary}\n\n"
        if summary
        else ""
    )

    resp = await _llm.ainvoke(
        [
            SystemMessage(
                content=(
                    "You are the Chief Knowledge Officer assistant. "
                    "The user is chatting casually. Be brief and polite, "
                    "and let them know you can answer from company documents or the web."
                )
            ),
            HumanMessage(content=f"{history}User: {question}"),
        ]
    )

    return {
        "final_answer": {
            "routing": "casual",
            "agent_name": "Casual Agent",
            "casual_answer": resp.content,
        }
    }
