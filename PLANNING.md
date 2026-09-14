# Project Planning & Roadmap

## Architecture
Frontend (HTML/JS) → FastAPI (api/ → services/ → repositories/) → MySQL
│
└─→ rag/ (ingestion, chunking, embeddings,
retrieval, reranking, generation, prompts)
│ │
Qdrant LLM Provider (configurable)


- `api/` — HTTP layer only (routes, status codes, request validation)
- `services/` — business logic, orchestrates repositories + rag/
- `repositories/` — the only layer that talks to the database
- `rag/` — the AI pipeline, built by hand (not hidden behind a framework) so every
  step is understandable and swappable

## Tech Choices

| Component | Choice | Why |
|---|---|---|
| API | FastAPI | Async, auto OpenAPI docs, Pydantic validation |
| Database | MySQL + SQLAlchemy + Alembic | Relational integrity, versioned schema |
| Vector DB | Qdrant | Free, self-hostable, strong metadata filtering (needed for per-user/per-document scoping) |
| Embeddings | Configurable (local sentence-transformers by default) | Swappable without rewriting the app |
| LLM | Configurable via env var (Gemini/OpenAI/Anthropic/local) | Same reasoning — provider is never hardcoded |
| Reranker | Optional cross-encoder | Toggleable for the "with vs without" experiment |
| Auth | JWT + bcrypt | Stateless, standard, easy to protect routes |
| Deployment | Docker Compose (api + mysql + qdrant) | One-command local stack |

## Development Phases

| Phase | Deliverable | Status |
|---|---|---|
| 0 | Docker Compose skeleton, config.py, health check | ✅ Done |
| 1 | DB models, Alembic migrations, JWT auth (register/login/me) | ✅ Done |
| 2 | Document upload + text extraction (pdf/docx/txt) + status tracking | ✅ Done |
| 3 | Chunking strategy (configurable, sentence/page-aware) | ✅ Done |
| 4 | Embeddings + Qdrant storage | ⬜ |✅ Done |
| 5 | Semantic retrieval + `/search` endpoint | ⬜ |🔧 In progress | 
| 6 | LLM provider abstraction + RAG answer generation + prompt design | ⬜ |
| 7 | Source citations end-to-end | ⬜ |
| 8 | Chat system: conversations, multi-turn history strategy | ⬜ |
| 9 | Multi-document selection & retrieval | ⬜ |
| 10 | Reranking (optional stage) | ⬜ |
| 11 | BM25 keyword search + comparison with semantic | ⬜ |
| 12 | Security hardening (validation, limits, prompt-injection defenses, rate limiting) | ⬜ |
| 13 | Evaluation framework (retrieval + generation metrics) | ⬜ |
| 14 | Hallucination test suite | ⬜ |
| 15 | Experiments (chunk size, top-k, embeddings, semantic vs BM25, rerank on/off) | ⬜ |
| 16 | Observability/logging | ⬜ |
| 17 | Tests (unit + integration) | ⬜ |
| 18 | Frontend | ⬜ |
| 19 | Docker Compose polish + final README | ⬜ |

## MVP vs Advanced

**MVP** (phases 0–8): upload a document, ask a question, get a grounded answer with
citations, multi-turn chat.

**Advanced** (phases 9–17): multi-doc reasoning, reranking, BM25 comparison, evaluation
suite, hallucination tests, experiments, security hardening, observability.

## Database Schema
users(id, email, hashed_password, created_at)
documents(id, user_id→users, filename, file_type, file_size, storage_path,
status, error_message, page_count, uploaded_at, processed_at)
document_chunks(id, document_id→documents, chunk_index, page_number, content,
token_count, embedding_model, created_at)
conversations(id, user_id→users, title, document_ids [JSON], created_at, updated_at)
messages(id, conversation_id→conversations, role, content, sources [JSON], created_at)

(Evaluation tables — `evaluation_runs`, `evaluation_results` — added in Phase 13.)

## API Design (target — grows per phase)

POST /auth/register ✅
POST /auth/login ✅
GET /auth/me ✅

POST   /documents/upload          ✅
GET    /documents                 ✅
GET    /documents/{id}            ✅
DELETE /documents/{id}            ✅
GET    /documents/{id}/status    (folded into GET /documents/{id})

POST /chat Phase 6
GET /conversations Phase 8
POST /conversations
GET /conversations/{id}
DELETE /conversations/{id}

POST /search Phase 5

POST /evaluation/run Phase 13
GET /evaluation/results

