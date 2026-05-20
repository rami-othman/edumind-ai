
# AGENTS.md — EduMind AI Service

## Project Name

EduMind AI Service

## Project Goal

Build the AI backend service for EduMind, an AI-powered educational platform for Syrian students.

The AI service is responsible for:

- Admin educational content ingestion.
- PDF text extraction.
- Arabic text cleaning and chunking.
- Embedding generation.
- Vector database storage.
- Retrieval-Augmented Generation.
- Arabic AI tutoring answers.
- Source-based answers with citations.
- Exam generation from uploaded content.
- Future answer evaluation and learning feedback.

Important: In the current system scope, there is no teacher role. Content is uploaded by admins only.

---

## Current Development Style

Work milestone by milestone.

Do not implement future features unless explicitly requested.

When a task is requested:

1. Read this file first.
2. Read `PROJECT_STATUS.md`.
3. Inspect the relevant files before editing.
4. Modify only the files needed for the current task.
5. Keep changes small and focused.
6. Update `PROJECT_STATUS.md` after meaningful changes.
7. Explain briefly what changed and how to test it.

Avoid unnecessary long explanations in the final response.

---

## Final Architecture Rule

The project uses the approved complex modular architecture.

Do not simplify, rename, or restructure folders unless explicitly requested.

Main structure:

```txt
app/
├── api/
├── core/
├── prompts/
├── repositories/
├── schemas/
├── services/
│   ├── embeddings/
│   ├── exams/
│   ├── ingestion/
│   ├── llm/
│   ├── rag/
│   └── vector_store/
└── utils/
```

Use the existing file tree as the source of truth.

---

## Current Scope

The current phase is the AI MVP foundation.

Build only what is needed for:

1. Dockerized FastAPI AI service.
2. Dockerized ChromaDB.
3. Dockerized Ollama.
4. PDF ingestion pipeline.
5. RAG question-answering endpoint.
6. Arabic answer generation.
7. Source metadata support.
8. Exam generation later.

Do not build advanced features yet unless explicitly requested.

Do not build:

- Teacher accounts.
- Teacher style adaptation.
- Student personalization.
- Advanced analytics.
- Full adaptive learning.
- Complex admin dashboards.
- Image generation.
- Authentication logic.
- Payment, subscriptions, or unrelated platform logic.

---

## Technology Stack

Use:

- Python 3.11
- FastAPI
- Pydantic / pydantic-settings
- ChromaDB
- Ollama
- PyMuPDF for PDF extraction
- Docker
- Docker Compose
- pytest for testing

Preferred architecture:

- FastAPI handles API routes.
- ChromaDB stores document chunks and embeddings.
- Ollama runs the local LLM and embedding models.
- Laravel/main backend will later communicate with this AI service through HTTP APIs.

---

## Docker-First Rule

The project must be designed to run with Docker from the beginning.

Expected services:

- `ai-service`
- `chroma`
- `ollama`

The service should run using:

```bash
docker compose up --build
```

Do not assume developers will run ChromaDB or Ollama manually outside Docker.

---

## Environment Configuration Rules

All configurable values must come from environment variables.

Do not hardcode:

- model names
- service URLs
- ports
- collection names
- chunk sizes
- retrieval `TOP_K`
- upload paths
- processed paths

Expected `.env.example` keys:

```env
APP_NAME=EduMind AI Service
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8001

CHROMA_HOST=chroma
CHROMA_PORT=8000
CHROMA_COLLECTION_NAME=edumind_content

OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_LLM_MODEL=gemma3:12b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

UPLOAD_DIR=/app/data/uploads
PROCESSED_DIR=/app/data/processed

CHUNK_SIZE=800
CHUNK_OVERLAP=150
TOP_K=5
```

Do not put secrets in `.env.example`.

Do not commit `.env`.

---

## File Responsibility Rules

API route files should only handle HTTP request/response flow.

Business logic belongs in services.

Use this responsibility map:

```txt
app/api/                  → FastAPI routes only
app/core/                 → logging, constants, exceptions
app/schemas/              → Pydantic request/response schemas
app/services/ingestion/   → PDF extraction, cleaning, chunking, metadata
app/services/embeddings/  → embedding generation
app/services/vector_store/→ ChromaDB client and storage/search logic
app/services/llm/         → LLM provider/client logic
app/services/rag/         → retrieval, prompt building, citations, RAG orchestration
app/services/exams/       → exam generation and answer evaluation
app/repositories/         → persistence abstractions when needed
app/prompts/              → prompt templates
app/utils/                → shared utility functions
```

Do not put large logic inside `app/main.py`.

Do not put business logic directly inside route files.

---

## LLM Layer Rule

The LLM layer must stay separate.

RAG services should not depend directly on Ollama implementation details.

Correct flow:

```txt
rag_service.py
→ llm_service.py
→ ollama_client.py
```

This allows future switching to:

- Ollama
- paid API
- local LLM server
- OpenAI-compatible API
- vLLM later if needed

Do not hardcode provider-specific logic outside `app/services/llm/`.

---

## RAG Rules

The RAG flow should be:

```txt
Student question
→ embed question
→ retrieve relevant chunks from ChromaDB
→ build strict Arabic prompt
→ send prompt to LLM
→ return answer + sources
```

The model must answer using only retrieved context.

If retrieved context is not enough, return:

```txt
لا أملك معلومات كافية من المحتوى المتوفر للإجابة بدقة.
```

Do not allow unsupported curriculum claims.

---

## Arabic Tutor Rules

Answers should:

1. Be in clear Arabic.
2. Be suitable for Syrian students.
3. Explain step by step when needed.
4. Use simple examples when helpful.
5. Stay grounded in uploaded content.
6. Mention sources when available.
7. Avoid unsupported claims.
8. Avoid long unnecessary introductions.

---

## Source Citation Rules

Every RAG answer should include source metadata when available.

Example response:

```json
{
  "answer": "قانون أوم يوضح العلاقة بين التوتر والتيار والمقاومة...",
  "sources": [
    {
      "file_name": "physics_book.pdf",
      "page_number": 45,
      "chunk_index": 12
    }
  ]
}
```

Sources must come from retrieved chunks, not from the LLM imagination.

---

## Coding Rules

Follow these rules:

1. Keep files focused.
2. Use type hints.
3. Use Pydantic schemas for API payloads.
4. Use readable function names.
5. Use environment settings through `config.py`.
6. Do not silently ignore exceptions.
7. Do not add unrelated dependencies.
8. Do not add authentication unless requested.
9. Do not add frontend/backend Laravel logic here.
10. Keep Arabic text processing safe and avoid damaging meaning.
11. Do not commit uploaded PDFs, processed files, Chroma data, Ollama models, caches, or `.env`.

---

## Testing Rules

When implementing a task, add or update lightweight tests when practical.

Use:

```bash
pytest
```

For FastAPI endpoints, use `TestClient`.

For each completed task, mention:

- how to run it
- how to test it
- expected result

---

## Documentation Rules

Always update `PROJECT_STATUS.md` after meaningful changes.

`PROJECT_STATUS.md` should include:

- current milestone
- implemented items
- not implemented yet
- modified files
- how to run
- how to test
- known issues
- next recommended step

Keep `README.md` practical and updated when setup or usage changes.

---

## Current Milestones

### Milestone 1A — FastAPI Foundation

- FastAPI app initialization
- `/health` endpoint
- settings loader
- basic tests

### Milestone 1B — Docker Foundation

- Dockerfile
- entrypoint
- docker-compose
- `ai-service`, `chroma`, and `ollama` containers

### Milestone 1C — Dependency Health Checks

- check ChromaDB reachability
- check Ollama reachability

### Milestone 2 — Content Ingestion

- PDF extraction
- Arabic text cleaning
- chunking
- metadata builder

### Milestone 3 — Vector Storage

- embeddings
- ChromaDB storage
- search/retrieval

### Milestone 4 — Basic RAG Chat

- retrieve chunks
- build prompt
- call LLM
- return Arabic answer with sources

### Milestone 5 — Exam Generation

- generate exam from selected content
- return questions, answers, explanations, and sources

---

## Codex Response Rules

After completing a task, respond with:

1. Summary of changes.
2. Modified files.
3. How to run.
4. How to test.
5. Assumptions or issues.
6. Next recommended step.

Keep the response concise.

Do not include long explanations unless there is an important design decision or error.

---

## Important Constraints

- Current project has no teacher feature.
- Admin uploads content.
- AI must be Arabic-first.
- AI must be source-grounded.
- Docker is required from the beginning.
- Keep implementation milestone-based.
- Do not over-engineer implementation even if the architecture is modular.
