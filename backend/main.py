"""
FastAPI Application Entry Point
────────────────────────────────
Chief Knowledge Officer  RAG Backend
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import documents, query, sessions, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # Lazy-init is fine for Supabase & ChromaDB clients.
    # Tables must already exist (see SQL in database.py and README).
    yield


app = FastAPI(
    title="Chief Knowledge Officer RAG API",
    description=(
        "Enterprise RAG system with per-user document isolation, "
        "global knowledge base, and intelligent web-search fallback. "
        "Built with LangGraph + OpenAI + Supabase."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(documents.router, tags=["Documents"])
app.include_router(query.router)
app.include_router(sessions.router)
app.include_router(auth.router, prefix="/auth", tags=["Auth"])


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "Chief Knowledge Officer RAG API"}
