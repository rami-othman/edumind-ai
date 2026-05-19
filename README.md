# EduMind AI Service

EduMind AI Service is the AI backend foundation for EduMind, an AI-powered educational platform for Syrian students.

The service will support admin educational content ingestion, PDF text extraction, Arabic text cleaning and chunking, embedding generation, vector storage, retrieval-augmented Arabic tutoring answers with source citations, and future exam generation.

## Current Status

Architecture scaffold only. No business logic has been implemented yet.

## Architecture Direction

The project is Docker-first and will be built around three future services:

- `ai-service`: FastAPI application for API routes and orchestration.
- `chroma`: ChromaDB vector database for document chunks and embeddings.
- `ollama`: Local LLM and embedding model runtime.

The Laravel/main backend will later communicate with this service over HTTP APIs.

## Folder Structure

```txt
app/                  FastAPI application package and service modules
app/api/              Route placeholders
app/core/             Logging, constants, and exception placeholders
app/schemas/          Pydantic schema placeholders
app/services/         Ingestion, embeddings, vector store, LLM, RAG, and exam service placeholders
app/prompts/          Prompt template placeholders
app/repositories/     Repository placeholders
app/utils/            Utility placeholders
data/                 Local upload, processed, and sample data directories
scripts/              Manual operation script placeholders
tests/                Test placeholders
docker/               Dockerfile and entrypoint placeholders
```

## Scope Notes

The current system has no teacher role. Content is uploaded by admins only.

This scaffold intentionally does not include FastAPI route logic, PDF extraction, ChromaDB integration, Ollama integration, RAG behavior, citations, exam generation, or answer evaluation.

## Next Recommended Step

Implement the minimal FastAPI foundation:

- Create working `app/main.py`.
- Add a `/health` endpoint.
- Add config loading from environment variables.
- Add a basic Dockerfile.
- Add working `docker-compose.yml`.
