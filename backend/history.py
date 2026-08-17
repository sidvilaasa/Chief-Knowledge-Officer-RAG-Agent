"""
Rolling conversation summary for the RAG agents.

Each turn stores: previous summary + current Q/A, capped at ~1024 tokens.
No extra LLM call — we keep the newest context and trim the oldest text.
"""
from __future__ import annotations

MAX_HISTORY_TOKENS = 1024
CHARS_PER_TOKEN = 4  # conservative English approximation
MAX_HISTORY_CHARS = MAX_HISTORY_TOKENS * CHARS_PER_TOKEN


def compact_history(previous_summary: str | None, question: str, answer: str) -> str:
    """
    Build an updated rolling summary under 1024 tokens.

    Keeps the previous summary plus the latest user/assistant turn.
    If the combined text exceeds the budget, the oldest characters of the
    previous summary are dropped so the latest turn is always retained.
    """
    prev = (previous_summary or "").strip()
    turn = f"User: {question.strip()}\nAssistant: {answer.strip()}".strip()
    if not turn:
        return prev[:MAX_HISTORY_CHARS]

    if prev:
        combined = f"{prev}\n{turn}"
    else:
        combined = turn

    if len(combined) <= MAX_HISTORY_CHARS:
        return combined

    # Always keep the latest turn; trim from the front of the old summary.
    separator = "\n"
    room = MAX_HISTORY_CHARS - len(turn) - len(separator)
    if room <= 0:
        return turn[-MAX_HISTORY_CHARS:]

    trimmed_prev = prev[-room:] if len(prev) > room else prev
    # Drop a partial first line so we don't start mid-sentence when possible.
    nl = trimmed_prev.find("\n")
    if nl != -1 and nl < len(trimmed_prev) - 1:
        trimmed_prev = trimmed_prev[nl + 1 :]
    return f"{trimmed_prev}{separator}{turn}"[-MAX_HISTORY_CHARS:]
