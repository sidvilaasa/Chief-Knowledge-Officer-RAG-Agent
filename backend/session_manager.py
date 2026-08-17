"""
Session Manager
───────────────
All CRUD operations for sessions and chat_messages stored in Supabase.

Rules enforced here:
  • Max MAX_SESSIONS_PER_USER  sessions per user  — LRU eviction
  • Max MAX_MESSAGES_PER_SESSION messages per session — sliding-window trim
"""
from __future__ import annotations

import logging
from typing import Optional

from database import MAX_MESSAGES_PER_SESSION, MAX_SESSIONS_PER_USER, get_supabase

logger = logging.getLogger(__name__)


# ── Session CRUD ──────────────────────────────────────────────────────────────

async def get_or_create_session(
    user_id: str,
    session_id: Optional[str] = None,
) -> dict:
    """
    Return an existing session dict or create a new one.

    If *session_id* is provided and belongs to *user_id*, return it.
    Otherwise create a new session, enforcing the per-user cap via LRU eviction.
    """
    sb = get_supabase()

    # ── Try to reuse the requested session ───────────────────────────────────
    if session_id:
        resp = (
            sb.table("sessions")
            .select("*")
            .eq("id", session_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        if resp.data:
            return resp.data[0]

    # ── Enforce session cap before creating ──────────────────────────────────
    await _enforce_session_cap(user_id)

    # ── Create new session ───────────────────────────────────────────────────
    resp = (
        sb.table("sessions")
        .insert({"user_id": user_id})
        .execute()
    )
    return resp.data[0]


async def _enforce_session_cap(user_id: str) -> None:
    """Delete the LRU session when the user is at the MAX_SESSIONS_PER_USER limit."""
    sb = get_supabase()

    count_resp = (
        sb.table("sessions")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .execute()
    )
    count = count_resp.count or 0

    if count >= MAX_SESSIONS_PER_USER:
        lru_resp = (
            sb.table("sessions")
            .select("id")
            .eq("user_id", user_id)
            .order("last_used_at", desc=False)
            .limit(1)
            .execute()
        )
        if lru_resp.data:
            lru_id = lru_resp.data[0]["id"]
            logger.info("LRU eviction: deleting session %s for user %s", lru_id, user_id)
            sb.table("sessions").delete().eq("id", lru_id).execute()


async def touch_session(session_id: str) -> None:
    """Update last_used_at to now so this session is the MRU."""
    sb = get_supabase()
    sb.table("sessions").update({"last_used_at": "now()"}).eq("id", session_id).execute()


async def set_session_title(session_id: str, title: str) -> None:
    """Set the session title (called once with the first question)."""
    sb = get_supabase()
    sb.table("sessions").update({"title": title[:200]}).eq("id", session_id).execute()


async def set_session_summary(session_id: str, summary: str) -> None:
    """Persist the rolling conversation summary (≤1024 tokens)."""
    sb = get_supabase()
    sb.table("sessions").update({"conversation_summary": summary}).eq("id", session_id).execute()


async def delete_session(session_id: str, user_id: str) -> bool:
    """
    Hard-delete a session (cascade deletes its messages).
    Returns True if a row was deleted, False if not found / not owned.
    """
    sb = get_supabase()
    resp = (
        sb.table("sessions")
        .delete()
        .eq("id", session_id)
        .eq("user_id", user_id)
        .execute()
    )
    return bool(resp.data)


async def list_sessions(user_id: str) -> list[dict]:
    """Return all sessions for *user_id* ordered by most-recently-used first."""
    sb = get_supabase()
    resp = (
        sb.table("sessions")
        .select("*")
        .eq("user_id", user_id)
        .order("last_used_at", desc=True)
        .execute()
    )
    return resp.data or []


# ── Message CRUD ──────────────────────────────────────────────────────────────

async def add_messages(
    session_id: str,
    user_question: str,
    assistant_answer: str,
    citations: list[str] | None = None,
    agent_name: str | None = None,
) -> None:
    """
    Insert a user + assistant message pair, then trim to the sliding window.

    Citations and agent_name are stored on the assistant row so they reload
    with session history.
    """
    sb = get_supabase()

    sb.table("chat_messages").insert([
        {
            "session_id": session_id,
            "role": "user",
            "content": user_question,
            "citations": [],
            "agent_name": None,
        },
        {
            "session_id": session_id,
            "role": "assistant",
            "content": assistant_answer,
            "citations": citations or [],
            "agent_name": agent_name,
        },
    ]).execute()

    await _trim_messages(session_id)


async def _trim_messages(session_id: str) -> None:
    """Delete oldest messages until count <= MAX_MESSAGES_PER_SESSION."""
    sb = get_supabase()

    count_resp = (
        sb.table("chat_messages")
        .select("id", count="exact")
        .eq("session_id", session_id)
        .execute()
    )
    count = count_resp.count or 0
    excess = count - MAX_MESSAGES_PER_SESSION

    if excess <= 0:
        return

    oldest_resp = (
        sb.table("chat_messages")
        .select("id")
        .eq("session_id", session_id)
        .order("created_at", desc=False)
        .limit(excess)
        .execute()
    )
    ids_to_delete = [row["id"] for row in (oldest_resp.data or [])]
    if ids_to_delete:
        sb.table("chat_messages").delete().in_("id", ids_to_delete).execute()


async def get_history(session_id: str) -> list[dict]:
    """
    Return the last MAX_MESSAGES_PER_SESSION messages for *session_id*,
    ordered oldest→newest (ready to pass as chat_history to the LLM).
    """
    sb = get_supabase()
    resp = (
        sb.table("chat_messages")
        .select("role, content")
        .eq("session_id", session_id)
        .order("created_at", desc=False)
        .limit(MAX_MESSAGES_PER_SESSION)
        .execute()
    )
    return resp.data or []


async def get_full_history(session_id: str) -> list[dict]:
    """Return all messages for a session (for the /sessions/{id}/messages endpoint)."""
    sb = get_supabase()
    resp = (
        sb.table("chat_messages")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at", desc=False)
        .execute()
    )
    return resp.data or []
