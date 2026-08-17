from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel


# ──────────────────────────────────────────────
# Documents
# ──────────────────────────────────────────────

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


class InternalResult(BaseModel):
    answer: str
    citations: list[str]  # list of "filename (chunk X)"


class WebResult(BaseModel):
    answer: str
    citations: list[str]  # list of URLs


class QueryResponse(BaseModel):
    question: str
    routing: Literal["internal_only", "web_only", "blended", "casual"]
    internal: Optional[InternalResult] = None
    web: Optional[WebResult] = None
    casual_answer: Optional[str] = None
