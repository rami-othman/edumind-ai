# EduMind AI Service

EduMind AI Service is the AI backend foundation for EduMind, an AI-powered educational platform for Syrian students.

The service will support admin educational content ingestion, PDF text extraction, Arabic text cleaning and chunking, embedding generation, vector storage, retrieval-augmented Arabic tutoring answers with source citations, and future exam generation.

## Current Milestone

Milestone 5A - Admin PDF Ingestion API

## Implemented

- FastAPI app initialization
- Environment settings loader
- Basic logging setup
- Basic `/` endpoint
- Basic `/health` endpoint
- Dockerfile for the FastAPI service
- Docker Compose services for `ai-service`, `chroma`, and `ollama`
- Persistent Docker volumes for ChromaDB and Ollama
- `/health/dependencies` endpoint for lightweight dependency checks
- ChromaDB and Ollama reachability checks
- PDF existence and extension validation
- Page-by-page PDF text extraction with PyMuPDF
- 1-based extracted PDF page numbers
- Lightweight PDF extractor tests using generated temporary PDFs
- Conservative Arabic-safe text cleaner
- Whitespace, newline, repeated empty line, and simple punctuation spacing cleanup
- Lightweight text cleaner tests
- Page-based text chunker
- Chunk size and overlap support
- Page number, chunk index, and character position preservation
- Lightweight chunker tests
- Document metadata and chunk record models
- Flat metadata builder for future vector storage
- Lightweight metadata builder tests
- In-memory ingestion preview service
- Extraction, cleaning, chunking, and metadata connection
- Empty page tracking
- Lightweight ingestion preview tests with generated temporary PDFs
- Embedding provider configuration
- Ollama embedding client using `/api/embed`
- Embedding service abstraction
- Mocked embedding service tests
- Future Google embedding placeholder configuration
- ChromaDB client wrapper
- Collection get/create support with configurable distance function
- Vector store support for storing chunk records with precomputed embeddings
- Similar chunk query helper
- Mocked vector store service tests
- Ingestion preview to vector store orchestration
- Chunk text embedding step
- Chunk record storage step
- Ingestion storage result model
- Zero-chunk ingestion storage handling
- Mocked ingestion-to-vector-store tests
- Retriever service for source chunk lookup
- Retrieved chunk model
- Query embedding flow
- Vector store similarity query flow
- Retrieval `top_k` support
- Retrieval `where` filter pass-through
- Mocked retriever tests
- Arabic tutor prompt builder
- Retrieved context formatting
- Source metadata extraction
- Fallback/no-context prompt behavior
- Prompt builder tests
- Ollama chat client foundation
- LLM service abstraction
- RAG answer result model
- Retriever to prompt builder to LLM orchestration
- RAG source preservation
- Mocked LLM and RAG orchestration tests
- `/api/v1/chat/ask` endpoint
- Chat request and response schemas
- RAG service dependency injection for routes
- Basic chat endpoint error handling
- Chat endpoint tests with mocked RAG service
- Manual real RAG smoke test script
- Real PDF ingestion path for smoke testing
- Real local Ollama embedding call path
- Real ChromaDB storage path
- Real RAG answer path through Ollama Cloud
- Smoke test CLI configuration overrides
- `/api/v1/ingest/pdf` endpoint
- Server-local books directory ingestion
- Subject inference from parent folder names
- Books metadata settings for grade, language, and source type
- Ingestion service dependency injection for routes
- Directory ingestion response schema
- Ingestion endpoint tests with mocked ingestion service

## Planned Architecture

The project is Docker-first and now runs three services:

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

This milestone intentionally does not include OCR, authentication, role management, automatic large book ingestion, Google embedding provider, chat history, exam generation, or answer evaluation.

ChromaDB and Ollama run as containers, but models are not auto-pulled.

## PDF Extraction Foundation

The project can now extract text from PDF files page by page using PyMuPDF.

Large book PDFs should be placed locally under:

`data/uploads/books/`

They are ignored by Git and should not be committed.

Current limitation:
- OCR is not implemented yet.
- Scanned/image-only PDFs may return empty text.

## Arabic Text Cleaning

The project includes a conservative Arabic-safe text cleaner in:

`app/services/ingestion/text_cleaner.py`

It normalizes whitespace, newlines, repeated empty lines, and simple punctuation spacing while preserving Arabic meaning.

Current limitation:
- It does not perform OCR.
- It does not remove diacritics.
- It does not aggressively normalize Arabic letters.
- It does not modify equations.

## Chunking Foundation

The project includes a text chunker in:

`app/services/ingestion/chunker.py`

It splits cleaned page text into ordered chunks while preserving:
- page number
- chunk index
- character positions
- overlap between chunks

Current limitation:
- Semantic chunking is not implemented yet.
- Chunking is page-based for safety with large PDFs.

## Metadata Builder

The project includes a metadata builder in:

`app/services/ingestion/metadata_builder.py`

It converts `TextChunk` objects into flat chunk records ready for future embedding and ChromaDB storage.

Each chunk record includes:
- unique chunk ID
- chunk text
- document metadata
- page number
- chunk index
- character positions

Current limitation:
- It does not store records in ChromaDB yet.
- It does not generate document IDs automatically yet.

## Ingestion Pipeline Preview

The project can now run an in-memory ingestion preview:

PDF extraction -> Arabic text cleaning -> chunking -> metadata records

This prepares content for future embeddings and ChromaDB storage.

Current limitation:
- API ingestion is single-PDF only.
- OCR is not implemented yet.
- Batch large-book ingestion is not implemented yet.

## Embedding Client Foundation

The project now includes an embedding abstraction in:

`app/services/embeddings/`

Current provider:
- Ollama local embeddings using `/api/embed`

Default model:
- `nomic-embed-text`

Future provider planned:
- Google Gemini Embedding 2

Current limitation:
- Google embedding provider is not implemented yet.

## ChromaDB Vector Store Foundation

The project now includes a vector store foundation in:

`app/services/vector_store/`

It supports:
- creating/getting a ChromaDB collection
- storing chunk records with precomputed embeddings
- querying similar chunks by query embedding

Current limitation:
- Tests use mocks and do not require a real ChromaDB container.

## Ingestion to Vector Store Integration

The project can now connect:

PDF extraction -> cleaning -> chunking -> metadata -> embeddings -> ChromaDB vector store

This stores chunk records with precomputed embeddings.

Current limitation:
- Tests use fakes/mocks and do not require real Ollama or ChromaDB.

## Retriever Foundation

The project now includes a retriever in:

`app/services/rag/retriever.py`

It embeds a user question, queries similar chunks from the vector store, and returns normalized retrieved source chunks.

Current limitation:
- Unit tests mock vector store calls.

## RAG Prompt Builder

The project now includes a prompt builder in:

`app/services/rag/prompt_builder.py`

It builds Arabic, source-grounded tutor prompts from retrieved chunks.

Current limitation:
- It does not call the LLM yet.
- It does not generate final answers yet.
- It is not connected to the chat API yet.

## RAG Service Orchestration

The project now connects:

retriever -> prompt builder -> LLM service

The current LLM provider is Ollama. The project can use local Ollama models or Ollama Cloud models such as:

`deepseek-v4-pro:cloud`

Current limitation:
- Unit tests mock LLM calls.
- Real Ollama Cloud requires `OLLAMA_API_KEY` in `.env`.

## Chat API Endpoint

The project now exposes:

`POST /api/v1/chat/ask`

This endpoint calls the internal RAG service and returns:
- answer
- sources
- retrieved chunks

Current limitation:
- No authentication yet.
- No chat history yet.
- Tests use mocked RAG service.

Example request:

```bash
curl -X POST http://localhost:8001/api/v1/chat/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"ما هو قانون أوم؟\",\"top_k\":5,\"filters\":{\"subject\":\"physics\"}}"
```

## Real RAG Smoke Test

A manual smoke test script is available at:

`scripts/smoke_test_real_rag.py`

It runs:

PDF -> extraction -> cleaning -> chunking -> metadata -> embeddings -> ChromaDB -> retrieval -> LLM answer

This script uses real services and should not be run as part of unit tests.

Default output is concise: ingestion summary, answer, compact source lines, and short retrieved chunk previews.
Use `--verbose` to print full source JSON and full retrieved chunk metadata.

Docker mode:

```bash
docker compose up -d --build
docker compose exec ollama ollama pull nomic-embed-text
docker compose exec ai-service python scripts/smoke_test_real_rag.py --pdf /app/data/fake_pdfs/ohms_law_arabic.pdf
```

Verbose:

```bash
docker compose exec ai-service python scripts/smoke_test_real_rag.py --pdf /app/data/fake_pdfs/ohms_law_arabic.pdf --verbose
```

Host mode:

```bash
python scripts/smoke_test_real_rag.py \
  --pdf data/fake_pdfs/ohms_law_arabic.pdf \
  --chroma-host localhost \
  --embedding-base-url http://localhost:11434 \
  --llm-base-url https://ollama.com
```

Requirements:
- ChromaDB container running
- Ollama container running
- `nomic-embed-text` pulled in Ollama
- `OLLAMA_API_KEY` set in local `.env` for Ollama Cloud

## Admin Books Ingestion API

Endpoint:

`POST /api/v1/ingest/pdf`

This endpoint ingests PDF books already stored on the server.

Default directory:

`/app/data/uploads/books`

Expected structure:

```txt
data/uploads/books/
├── biology/
├── math/
└── physics/
```

Example:

```bash
curl -X POST http://localhost:8001/api/v1/ingest/pdf \
  -H "Content-Type: application/json" \
  -d "{}"
```

Optional custom directory:

```bash
curl -X POST http://localhost:8001/api/v1/ingest/pdf \
  -H "Content-Type: application/json" \
  -d "{\"books_dir\":\"/app/data/uploads/books\"}"
```

Metadata:
- grade comes from `BOOKS_GRADE`
- subject is inferred from folder name
- language comes from `BOOKS_LANGUAGE`
- source type comes from `BOOKS_SOURCE_TYPE`
- chunk settings come from `.env`

Current limitation:
- No authentication yet.
- No batch large-book ingestion yet.
- Endpoint tests use mocked ingestion service.

## Run With Docker

```bash
docker compose up --build
```

## Stop Docker

```bash
docker compose down
```

## Optional Future Model Pulls

```bash
docker compose exec ollama ollama pull gemma3:12b
docker compose exec ollama ollama pull nomic-embed-text
```

## Run Locally Without Docker

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## Test

```bash
docker compose up --build
curl http://localhost:8001/health
curl http://localhost:8001/health/dependencies
pytest tests/test_pdf_extractor.py -v
pytest tests/test_text_cleaner.py -v
pytest tests/test_chunker.py -v
pytest tests/test_metadata_builder.py -v
pytest tests/test_ingestion_service.py -v
pytest tests/test_embedding_service.py -v
pytest tests/test_vector_store_service.py -v
pytest tests/test_ingestion_to_vector_store.py -v
pytest tests/test_retriever.py -v
pytest tests/test_prompt_builder.py -v
pytest tests/test_llm_service.py -v
pytest tests/test_rag_service.py -v
pytest tests/test_chat_routes.py -v
pytest tests/test_ingest_routes.py -v
pytest -v
```

`/health` checks only the FastAPI app.

`/health/dependencies` checks FastAPI to ChromaDB and FastAPI to Ollama connectivity. This does not mean AI logic is implemented yet.

Expected `/health` response:

```json
{
  "status": "ok",
  "service": "EduMind AI Service",
  "environment": "development",
  "version": "0.1.0"
}
```

## Next Recommended Step

Milestone 5B - Real Admin Ingestion Smoke Test.
