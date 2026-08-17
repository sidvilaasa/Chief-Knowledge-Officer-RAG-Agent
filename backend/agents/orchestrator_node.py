"""
Orchestrator Node
─────────────────
Decides whether the query is casual chat or requires RAG.

Uses a fast heuristic first so greetings skip an extra LLM round-trip.
"""
from __future__ import annotations

import re

CASUAL_RE = re.compile(
    r"^\s*("
    r"hi|hello|hey|yo|sup|hiya|"
    r"thanks|thank you|thx|"
    r"good (morning|afternoon|evening|night)|"
    r"how are you( doing)?|how's it going|"
    r"who are you|what('?s| is) your name|"
    r"ok|okay|cool|great|nice|"
    r"bye|goodbye|see you"
    r")[\s!.?]*$",
    re.IGNORECASE,
)


async def orchestrator_node(state: dict) -> dict:
    question = (state.get("question") or "").strip()
    if not question or CASUAL_RE.match(question):
        return {"orchestration": "casual"}
    return {"orchestration": "rag"}
