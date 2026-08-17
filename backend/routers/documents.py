"""
Documents Router
────────────────
Endpoints:
  POST /documents/upload-user-doc    – upload private document
  POST /documents/upload-global-doc  – upload global document
  GET  /documents/my-docs            – list caller's private docs
  GET  /documents/global-docs        – list all global docs
  GET  /documents/accessible         – list own + global docs
  DELETE /documents/{doc_id}         – delete own document
"""
from __future__ import annotations
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from auth import get_current_user
from database import get_supabase
from ingest import delete_document, ingest_document
from models import DocumentListResponse, DocumentMeta, UploadResponse

router = APIRouter(prefix="/documents", tags=["Documents"])


# ── Upload ────────────────────────────────────────────────────────────────────

@router.post("/upload-user-doc", response_model=UploadResponse)
async def upload_user_doc(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
):
    """Upload a private document scoped to the calling user."""
    _validate_file(file)
    data = await file.read()
    doc_id = await ingest_document(
        file_bytes=data,
        filename=file.filename,
        scope="user",
        user_id=user_id,
    )
    storage_path = f"{user_id}/{file.filename}"
    return UploadResponse(
        message="User document ingested successfully.",
        document_id=UUID(doc_id),
        storage_path=storage_path,
    )


@router.post("/upload-global-doc", response_model=UploadResponse)
async def upload_global_doc(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),  # auth still required
):
    """Upload a global document accessible to all users."""
    _validate_file(file)
    data = await file.read()
    doc_id = await ingest_document(
        file_bytes=data,
        filename=file.filename,
        scope="global",
        user_id=None,
    )
    return UploadResponse(
        message="Global document ingested successfully.",
        document_id=UUID(doc_id),
        storage_path=f"global/{file.filename}",
    )


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("/my-docs", response_model=DocumentListResponse)
async def list_my_docs(user_id: str = Depends(get_current_user)):
    """List documents uploaded by the calling user."""
    sb = get_supabase()
    result = (
        sb.table("documents")
        .select("*")
        .eq("user_id", user_id)
        .eq("scope", "user")
        .order("created_at", desc=True)
        .execute()
    )
    docs = [DocumentMeta(**row) for row in result.data]
    return DocumentListResponse(documents=docs, total=len(docs))


@router.get("/global-docs", response_model=DocumentListResponse)
async def list_global_docs(user_id: str = Depends(get_current_user)):
    """List all global documents accessible to every user."""
    sb = get_supabase()
    result = (
        sb.table("documents")
        .select("*")
        .eq("scope", "global")
        .order("created_at", desc=True)
        .execute()
    )
    docs = [DocumentMeta(**row) for row in result.data]
    return DocumentListResponse(documents=docs, total=len(docs))


@router.get("/accessible", response_model=DocumentListResponse)
async def list_accessible_docs(user_id: str = Depends(get_current_user)):
    """List all documents accessible to the caller (own + global)."""
    sb = get_supabase()
    # Own docs
    user_res = (
        sb.table("documents")
        .select("*")
        .eq("user_id", user_id)
        .eq("scope", "user")
        .execute()
    )
    # Global docs
    global_res = (
        sb.table("documents")
        .select("*")
        .eq("scope", "global")
        .execute()
    )
    combined = user_res.data + global_res.data
    # Sort by created_at descending
    combined.sort(key=lambda r: r["created_at"], reverse=True)
    docs = [DocumentMeta(**row) for row in combined]
    return DocumentListResponse(documents=docs, total=len(docs))


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_doc(
    doc_id: str,
    user_id: str = Depends(get_current_user),
):
    """Delete a document owned by the calling user (cascades Supabase + ChromaDB)."""
    sb = get_supabase()
    existing = (
        sb.table("documents")
        .select("id")
        .eq("id", doc_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or you do not have permission to delete it.",
        )
    await delete_document(doc_id=doc_id, user_id=user_id)


# ── Helpers ───────────────────────────────────────────────────────────────────

ALLOWED_EXTENSIONS = {"pdf", "txt", "docx", "doc", "md"}


def _validate_file(file: UploadFile) -> None:
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type '.{ext}'. Allowed: {ALLOWED_EXTENSIONS}",
        )
