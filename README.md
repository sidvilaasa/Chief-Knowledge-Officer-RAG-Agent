# Chief Knowledge Officer RAG

Enterprise chat assistant that answers from **your documents** first, then the **web** when internal knowledge is incomplete.

| Layer | Stack |
|---|---|
| Frontend | Angular 20 |
| Backend | FastAPI + LangGraph |
| Models | OpenAI |
| Search | ChromaDB (internal) + Tavily (web) |
| Storage | Supabase (Postgres + file buckets) |

---

## How a question is answered

```
User question
    │
    ▼
Orchestrator  →  casual chat  OR  RAG
    │
    ▼
Knowledge Agent  (ChromaDB: user docs + global docs)
    │
    ▼
Router
    ├── sufficient     → answer from documents only
    ├── partial        → documents + web search
    └── insufficient   → web search only
    │
    ▼
Blender  →  answer + citations + agent name
```

Sessions keep a rolling conversation summary (about 1024 tokens). Citations and the agent name are stored with each assistant message.

---

## Project layout

```
Chief-Knowledge-Officer-RAG-Agent/
├── backend/          FastAPI API
├── frontend/         Angular UI
└── README.md         this file
```

---

## Prerequisites

- Python ≥ 3.12
- Node.js 20+
- A [Supabase](https://supabase.com) project
- OpenAI API key
- Tavily API key ([tavily.com](https://tavily.com))

---

## 1. Backend setup

### Environment

Create `backend/.env`:

```env
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
CHROMA_PERSIST_DIR=./chroma_db
```

### Database

In the **Supabase SQL Editor**, run the `SQL_CREATE_TABLES` script from `backend/database.py` (documents, users, sessions, chat messages, citations, agent name, conversation summary).

If those tables already exist, still run the `ALTER TABLE` statements at the bottom of that SQL so citations and summaries persist.

### Storage buckets

In Supabase → **Storage**, create two **private** buckets:

- `user-documents`
- `global-documents`

### Install and run

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)  
Health: [http://localhost:8000/health](http://localhost:8000/health)

---

## 2. Frontend setup

API base URL is in `frontend/src/environments/environment.ts`.

- Local backend: `http://localhost:8000`
- Hosted backend: `https://your-fastapi-host.com` (no trailing slash)

```bash
cd frontend
npm install
npm start
```

Open [http://localhost:4200](http://localhost:4200).

HR users can upload **global** documents. Other users upload only their own files.

---

## 3. Deploy frontend on Vercel (Hobby / free)

Vercel hosts the Angular UI only. FastAPI must already be public (for example Render).

1. Set `apiBase` in `frontend/src/environments/environment.ts` to your live FastAPI origin.
2. Push this repo to GitHub.
3. On [vercel.com](https://vercel.com) → **Add New Project** → import the repo.
4. Use these settings:

| Setting | Value |
|---|---|
| Root Directory | `frontend` (or `Chief-Knowledge-Officer-RAG-Agent/frontend` if the repo parent is the Git root) |
| Framework Preset | Other |
| Build Command | `npm run build` |
| Output Directory | `dist/frontend/browser` |
| Install Command | `npm install` |

5. Click **Deploy**. Open the `*.vercel.app` URL.

`frontend/vercel.json` already rewrites Angular routes (`/login`, `/chat`) to `index.html`.

---

## API overview

Most routes need header `X-User-ID` after login (the UI sends it automatically).

### Auth

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/signup` | Create account (`username`, `password`, `department`: `HR` or `Employee`) |
| `POST` | `/auth/login` | Log in |

### Query

| Method | Path | Description |
|---|---|---|
| `POST` | `/query` | Run the RAG pipeline (`question`, optional `session_id`) |

### Sessions

| Method | Path | Description |
|---|---|---|
| `GET` | `/sessions` | List chats |
| `GET` | `/sessions/{id}/messages` | Load history (includes citations and agent name) |
| `DELETE` | `/sessions/{id}` | Delete a chat |

### Documents

| Method | Path | Description |
|---|---|---|
| `POST` | `/documents/upload-user-doc` | Upload a private document |
| `POST` | `/documents/upload-global-doc` | Upload a global document (HR) |
| `GET` | `/documents/my-docs` | List own documents |
| `GET` | `/documents/global-docs` | List global documents |
| `GET` | `/documents/accessible` | Own + global |
| `DELETE` | `/documents/{doc_id}` | Delete own document |

---

## Typical local workflow

1. Start FastAPI on port `8000`.
2. Point `environment.ts` at `http://localhost:8000`.
3. Start Angular on port `4200`.
4. Sign up / log in, upload a document, ask a question.
