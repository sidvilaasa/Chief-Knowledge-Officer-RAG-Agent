"""
Casual Talk Node
─────────────────
Responds to casual chit-chat directly.
"""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from config import settings

_llm = ChatOpenAI(
    model=settings.chat_model,
    api_key=settings.openai_api_key,
    temperature=0.7,
)

async def casual_node(state: dict) -> dict:
    question = state["question"]
    resp = await _llm.ainvoke([
        SystemMessage(content="You are a helpful Chief knowledgr officer RAG assistant. The user is just chatting casually right now. Say hi, be polite, and let them know you are ready to answer their information queries when they need it."),
        HumanMessage(content=question)
    ])
    
    return {
        "final_answer": {
            "routing": "casual",
            "casual_answer": resp.content
        }
    }
