"""
Document ingestion pipeline:
  1. Upload raw file to Supabase Storage (auto-creates user folder)
  2. Record metadata in the `documents` PostgreSQL table
  3. Chunk → embed → store in ChromaDB
  4. Record chunk IDs in `document_chunks` table
"""
from __future__ import annotations

import io
import uuid
from typing import Literal

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_openai import OpenAIEmbeddings

from config import settings
from database import GLOBAL_BUCKET, USER_BUCKET, get_collection, get_supabase

embeddings = OpenAIEmbeddings(
    model=settings.embedding_model,
    api_key=settings.openai_api_key,
)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap,
)


def _load_documents(file_bytes: bytes, filename: str) -> list:
    """Load a file into LangChain Document objects based on extension."""
    ext = filename.rsplit(".", 1)[-1].lower()

    # Write to a temp-like buffer for loaders that need a file path
    import tempfile, os
    suffix = f".{ext}"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        if ext == "pdf":
            docs = PyPDFLoader(tmp_path).load()
        elif ext in ("docx", "doc"):
            docs = Docx2txtLoader(tmp_path).load()
        else:
            docs = TextLoader(tmp_path, encoding="utf-8").load()
    finally:
        os.unlink(tmp_path)

    return docs


async def ingest_document(
    file_bytes: bytes,
    filename: str,
    scope: Literal["user", "global"],
    user_id: str | None,
) -> str:
    """
    Full ingestion pipeline. Returns the new document UUID.

    Supabase Storage path:
      - user docs  → user-documents/{user_id}/{filename}
      - global docs → global-documents/global/{filename}
    """
    sb = get_supabase()
    collection = get_collection()

    # ── 1. Build storage path (auto-creates user folder) ──────────────────────
    if scope == "user":
        bucket = USER_BUCKET
        storage_path = f"{user_id}/{filename}"
    else:
        bucket = GLOBAL_BUCKET
        storage_path = f"global/{filename}"

    # Upload (upsert=True handles re-uploads with same name)
    sb.storage.from_(bucket).upload(
        path=storage_path,
        file=file_bytes,
        file_options={"upsert": "true"},
    )

    # ── 2. Insert into documents table ─────────────────────────────────────────
    ext = filename.rsplit(".", 1)[-1].lower()
    doc_id = str(uuid.uuid4())

    sb.table("documents").insert(
        {
            "id": doc_id,
            "user_id": user_id,
            "scope": scope,
            "filename": filename,
            "storage_path": storage_path,
            "file_type": ext,
        }
    ).execute()

    # ── 3. Chunk & embed ───────────────────────────────────────────────────────
    raw_docs = _load_documents(file_bytes, filename)
    chunks = splitter.split_documents(raw_docs)

    if not chunks:
        return doc_id

    texts = [c.page_content for c in chunks]
    vectors = embeddings.embed_documents(texts)

    # ── 4. Store vectors in ChromaDB ───────────────────────────────────────────
    chroma_ids: list[str] = []
    chroma_metas: list[dict] = []
    for i, chunk in enumerate(chunks):
        cid = f"{doc_id}_chunk_{i}"
        chroma_ids.append(cid)
        chroma_metas.append(
            {
                "document_id": doc_id,
                "user_id": user_id or "",
                "scope": scope,
                "filename": filename,
                "chunk_index": i,
            }
        )

    collection.add(
        ids=chroma_ids,
        embeddings=vectors,
        documents=texts,
        metadatas=chroma_metas,
    )

    # ── 5. Record chunk rows in Supabase ──────────────────────────────────────
    chunk_rows = [
        {"document_id": doc_id, "chroma_id": cid, "chunk_index": i}
        for i, cid in enumerate(chroma_ids)
    ]
    sb.table("document_chunks").insert(chunk_rows).execute()

    return doc_id


async def delete_document(doc_id: str, user_id: str) -> None:
    """
    Delete a document owned by user_id:
      – removes vectors from ChromaDB
      – removes file from Supabase Storage
      – removes DB rows (cascade deletes chunks)
    """
    sb = get_supabase()
    collection = get_collection()

    # Fetch doc metadata
    result = (
        sb.table("documents")
        .select("*")
        .eq("id", doc_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    doc = result.data
    if not doc:
        return

    # Remove from ChromaDB
    chunks_res = (
        sb.table("document_chunks")
        .select("chroma_id")
        .eq("document_id", doc_id)
        .execute()
    )
    chroma_ids = [r["chroma_id"] for r in chunks_res.data]
    if chroma_ids:
        collection.delete(ids=chroma_ids)

    # Remove from Supabase Storage
    bucket = USER_BUCKET if doc["scope"] == "user" else GLOBAL_BUCKET
    sb.storage.from_(bucket).remove([doc["storage_path"]])

    # Remove from DB (cascade removes chunks)
    sb.table("documents").delete().eq("id", doc_id).execute()
