# Chief of Staff RAG Backend

Enterprise RAG system built with **FastAPI** + **LangGraph** + **OpenAI** + **Supabase** (Storage + PostgreSQL) + **ChromaDB**.

---

## Prerequisites

| Tool | Purpose |
|---|---|
| Python ≥ 3.12 | Runtime |
| [uv](https://docs.astral.sh/uv/) | Package manager |
| Supabase project | Storage + PostgreSQL |
| OpenAI API key | LLM + Embeddings |
| Tavily API key | Web search (free tier at [tavily.com](https://tavily.com)) |

---

## Setup

### 1. Fill in `.env`
```env
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
CHROMA_PERSIST_DIR=./chroma_db
```

### 2. Create Supabase tables
Open the **Supabase SQL Editor** and run the contents of:
```
backend/scripts/setup_tables.sql
```

### 3. Create Supabase Storage buckets
In the Supabase dashboard → Storage, create two buckets:
- `user-documents` (private)
- `global-documents` (private)

### 4. Install dependencies
```bash
cd /path/to/project
uv sync
```

### 5. Start the server
```bash
cd backend
uvicorn main:app --reload
```

API docs at → **http://localhost:8000/docs**

---

## API Reference

### Documents

| Method | Path | Header | Description |
|---|---|---|---|
| `POST` | `/documents/upload-user-doc` | `X-User-ID` | Upload private document (auto-creates user folder) |
| `POST` | `/documents/upload-global-doc` | `X-User-ID` | Upload global document |
| `GET` | `/documents/my-docs` | `X-User-ID` | List caller's private docs |
| `GET` | `/documents/global-docs` | `X-User-ID` | List all global docs |
| `GET` | `/documents/accessible` | `X-User-ID` | List all accessible docs (own + global) |
| `DELETE` | `/documents/{doc_id}` | `X-User-ID` | Delete own doc (cascades Storage + ChromaDB) |

### Query

| Method | Path | Header | Description |
|---|---|---|---|
| `POST` | `/query` | `X-User-ID` | Run the RAG pipeline |

**Query request body:**
```json
{ "question": "What is our Q3 revenue?" }
```

**Query response:**
```json
{
  "question": "...",
  "routing": "blended",        // "internal_only" | "web_only" | "blended"
  "internal": {
    "answer": "...",
    "citations": ["report.pdf (chunk 2)"]
  },
  "web": {
    "answer": "...",
    "citations": ["https://example.com/article"]
  }
}
```

---

## Architecture

```
POST /query
    │
    ▼
knowledge_agent  →  router  →  [web_search]  →  blender  →  response
    │               │
    │               ├── "complete"  → skip web, go to blender
    │               ├── "partial"   → web search + blend
    │               └── "none"      → web search only
    │
    └── ChromaDB filter: (user_id == me) OR (scope == global)
```

**Per-user folder**: On first upload, Supabase Storage auto-creates the `user-documents/{user_id}/` prefix. All vectors in ChromaDB are tagged with `user_id`, so RAG is always scoped to that user's folder plus global docs.

---

## File Structure

```
backend/
├── main.py              ← FastAPI app
├── config.py            ← env settings
├── models.py            ← Pydantic schemas
├── database.py          ← Supabase + ChromaDB clients
├── ingest.py            ← upload → chunk → embed → store
├── auth.py              ← X-User-ID header dependency
├── graph.py             ← LangGraph StateGraph
├── agents/
│   ├── knowledge_agent.py   ← vector search (user + global)
│   ├── router_node.py       ← LLM routing classifier
│   ├── web_search_agent.py  ← Tavily search
│   └── blender_node.py      ← final answer synthesis
├── routers/
│   ├── documents.py         ← upload / list / delete
│   └── query.py             ← POST /query
└── scripts/
    └── setup_tables.sql     ← run once in Supabase
```
