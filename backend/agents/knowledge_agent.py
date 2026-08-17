"""
Knowledge Agent Node
────────────────────
Searches ChromaDB for chunks accessible to the current user:
  - their own uploaded documents  (user_id == state.user_id)
  - all global documents          (scope == "global")

Returns ranked chunks with source citations.
"""
from __future__ import annotations

from langchain_openai import OpenAIEmbeddings

from config import settings
from database import get_collection


embeddings = OpenAIEmbeddings(
    model=settings.embedding_model,
    api_key=settings.openai_api_key,
)


async def knowledge_agent_node(state: dict) -> dict:
    """
    LangGraph node.
    Reads: state["question"], state["user_id"]
    Writes: state["internal_chunks"]  (list of dicts)
    """
    question: str = state["question"]
    user_id: str = state["user_id"]
    collection = get_collection()

    summary = (state.get("chat_history_summary") or "").strip()
    embed_text = (
        f"{summary[-800:]}\n\nCurrent question: {question}" if summary else question
    )

    # Embed the question (plus rolling history so follow-ups retrieve correctly)
    query_vector = await embeddings.aembed_query(embed_text)

    # Query ChromaDB – filter: user's own docs OR global docs
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=settings.retrieval_top_k,
        where={
            "$or": [
                {"user_id": {"$eq": user_id}},
                {"scope": {"$eq": "global"}},
            ]
        },
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    if results["documents"] and results["documents"][0]:
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            chunks.append(
                {
                    "text": doc,
                    "filename": meta.get("filename", "unknown"),
                    "chunk_index": meta.get("chunk_index", 0),
                    "scope": meta.get("scope", "user"),
                    "distance": dist,
                }
            )

    return {"internal_chunks": chunks}
