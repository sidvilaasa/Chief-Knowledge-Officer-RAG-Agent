"""
Sessions Router
───────────────
GET    /sessions                          – List all sessions for the current user
GET    /sessions/{session_id}/messages    – Get full message history for a session
DELETE /sessions/{session_id}             – Delete a session and all its messages
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from models import SessionListResponse, SessionMessagesResponse, SessionInfo, ChatMessage
from session_manager import delete_session, get_full_history, list_sessions

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("", response_model=SessionListResponse)
async def get_sessions(user_id: str = Depends(get_current_user)):
    """
    List all chat sessions for the authenticated user.
    Ordered by most-recently-used first (max 10 returned).
    """
    sessions = await list_sessions(user_id)
    return SessionListResponse(
        sessions=[SessionInfo(**s) for s in sessions],
        total=len(sessions),
    )


@router.get("/{session_id}/messages", response_model=SessionMessagesResponse)
async def get_session_messages(
    session_id: str,
    user_id: str = Depends(get_current_user),
):
    """Return the full message history for *session_id* (owned by the calling user)."""
    messages = await get_full_history(session_id)

    # Ensure at least one message exists & belongs to the user's session
    if not messages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or has no messages.",
        )

    return SessionMessagesResponse(
        session_id=session_id,
        messages=[ChatMessage(**m) for m in messages],
        total=len(messages),
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_session(
    session_id: str,
    user_id: str = Depends(get_current_user),
):
    """Delete a session and all its messages (irreversible)."""
    deleted = await delete_session(session_id, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or does not belong to you.",
        )
