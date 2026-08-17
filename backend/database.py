"""
Database layer: Supabase client (Storage + PostgreSQL) and ChromaDB client.
"""
from __future__ import annotations

import chromadb
from chromadb.config import Settings as ChromaSettings
from supabase import Client, create_client

from config import settings

# ──────────────────────────────────────────────
# Supabase
# ──────────────────────────────────────────────

_supabase_client: Client | None = None

USER_BUCKET = "user-documents"
GLOBAL_BUCKET = "global-documents"


def get_supabase() -> Client:
    """Return a singleton Supabase client."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_service_key,
        )
    return _supabase_client


# ──────────────────────────────────────────────
# ChromaDB
# ──────────────────────────────────────────────

_chroma_client: chromadb.PersistentClient | None = None
CHROMA_COLLECTION = "rag_documents"


def get_chroma() -> chromadb.PersistentClient:
    """Return a singleton ChromaDB persistent client."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _chroma_client


def get_collection() -> chromadb.Collection:
    """Return (or create) the shared ChromaDB collection."""
    client = get_chroma()
    return client.get_or_create_collection(
        name=CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


# ──────────────────────────────────────────────
# Supabase SQL helpers
# ──────────────────────────────────────────────

# ── Session management limits ────────────────────────────────────────────────
MAX_SESSIONS_PER_USER: int = 10
MAX_MESSAGES_PER_SESSION: int = 10  # sliding window (user + assistant each count as 1)


SQL_CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS documents (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      TEXT,
    scope        TEXT NOT NULL DEFAULT 'user',
    filename     TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    file_type    TEXT,
    created_at   TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id  UUID REFERENCES documents(id) ON DELETE CASCADE,
    chroma_id    TEXT NOT NULL,
    chunk_index  INT NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT now()
);

-- Store user credentials securely
CREATE TABLE IF NOT EXISTS app_users (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    department TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Store RAG sessions
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    title TEXT,
    conversation_summary TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    last_used_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role        TEXT NOT NULL,
    content     TEXT NOT NULL,
    citations   JSONB NOT NULL DEFAULT '[]'::jsonb,
    agent_name  TEXT,
    created_at  TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE sessions ADD COLUMN IF NOT EXISTS conversation_summary TEXT;
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS citations JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS agent_name TEXT;
"""


async def ensure_tables() -> None:
    """Create Supabase tables if they don't already exist (called at startup)."""
    sb = get_supabase()
    sb.rpc("exec_sql", {"sql": SQL_CREATE_TABLES}).execute()
