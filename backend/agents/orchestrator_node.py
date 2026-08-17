"""
Orchestrator Node
─────────────────
Decides whether the query is a casual conversation or requires RAG.
"""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from config import settings

_llm = ChatOpenAI(
    model=settings.chat_model,
    api_key=settings.openai_api_key,
    temperature=0.0,
)

PROMPT = """You are an orchestrator routing queries.
Determine if the user's input is just a casual greeting/conversation without a specific informational request (e.g. "hi", "how are you", "who are you"), or if it is a real question that requires searching the knowledge base.

Return EXACTLY ONE WORD:
- "casual" (if greeting/casual chat)
- "rag" (if it requires retrieving documents or answering a real question)

User Input: {question}"""

async def orchestrator_node(state: dict) -> dict:
    question = state["question"]
    resp = await _llm.ainvoke([
        SystemMessage(content="You classify user queries."),
        HumanMessage(content=PROMPT.format(question=question))
    ])
    
    val = resp.content.strip().lower()
    if "casual" in val:
        return {"orchestration": "casual"}
    return {"orchestration": "rag"}
