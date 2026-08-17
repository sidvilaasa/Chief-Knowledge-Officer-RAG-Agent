from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel


# ──────────────────────────────────────────────
# Documents
# ──────────────────────────────────────────────

class AuthRequest(BaseModel):
    username: str
    password: str
    department: Optional[str] = None  # Required for signup, optional for login

class AuthResponse(BaseModel):
    message: str
    username: str
    department: str

class DocumentMeta(BaseModel):
    id: UUID
    user_id: Optional[str]
    scope: Literal["user", "global"]
    filename: str
    storage_path: str
    file_type: Optional[str]
    created_at: datetime


class UploadResponse(BaseModel):
    message: str
    document_id: UUID
    storage_path: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentMeta]
    total: int


# ──────────────────────────────────────────────
# Query
# ──────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None  # omit to auto-create a new session


class InternalResult(BaseModel):
    answer: str
    citations: list[str]  # list of "filename (chunk X)"


class WebResult(BaseModel):
    answer: str
    citations: list[str]  # list of URLs


class QueryResponse(BaseModel):
    question: str
    session_id: str
    session_title: Optional[str] = None
    routing: Literal["internal_only", "web_only", "blended", "casual"]
    internal: Optional[InternalResult] = None
    web: Optional[WebResult] = None
    casual_answer: Optional[str] = None


# ──────────────────────────────────────────────
# Sessions
# ──────────────────────────────────────────────

class SessionInfo(BaseModel):
    id: str
    user_id: str
    title: Optional[str] = None
    created_at: datetime
    last_used_at: datetime


class ChatMessage(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime


class SessionListResponse(BaseModel):
    sessions: list[SessionInfo]
    total: int


class SessionMessagesResponse(BaseModel):
    session_id: str
    messages: list[ChatMessage]
    total: int
