# PROJECT_STATUS.md - EduMind AI Service

## Current Milestone
Milestone 4E - Real RAG Smoke Test Script

## Current Status Updates

### Improvement - Source Citation and Smoke Test Output Readability
- Improved source citation prompt rules for file name, page number, chunk index, subject, and lesson.
- Added concise smoke test output sections for ingestion, answer, sources, and retrieved chunk previews.
- Added `--verbose` mode for full source JSON and retrieved chunk metadata.
- Cleaned retrieved chunk previews by normalizing whitespace and truncating default previews.

## Implemented
- FastAPI app initialization
- Environment settings loader
- Basic logging setup
- Basic `/` endpoint
- Basic `/health` endpoint
- Dockerfile for the FastAPI service
- Docker entrypoint for Uvicorn startup
- Docker Compose services for `ai-service`, `chroma`, and `ollama`
- Persistent named volumes for ChromaDB and Ollama
- `/health/dependencies`
- ChromaDB reachability check
- Ollama reachability check
- Lightweight mocked dependency health tests
- PDF existence validation
- PDF extension validation
- Page-by-page text extraction with PyMuPDF
- 1-based page numbers
- Page count and file name extraction
- Lightweight tests with generated PDF
- Conservative Arabic-safe text cleaner
- Whitespace normalization
- Repeated empty line cleanup
- Simple Arabic punctuation spacing cleanup
- Tests for text cleaning behavior
- Text chunk dataclass/model
- Page-based text chunking
- Chunk size support
- Chunk overlap support
- Page number preservation
- Chunk index preservation
- Character position tracking
- Validation tests for chunking behavior
- Document metadata model
- Chunk record model
- Chunk ID builder
- Flat metadata builder
- Metadata validation
- Chunk records ready for future vector storage
- Tests for metadata behavior
- Ingestion preview service
- Extraction + cleaning + chunking + metadata connection
- Empty page tracking
- Chunk record generation
- Tests with generated temporary PDF
- Embedding provider configuration
- Ollama embedding client
- Embedding service abstraction
- Mocked embedding tests
- Future Google embedding placeholder configuration
- ChromaDB client wrapper
- Collection get/create support
- Configurable ChromaDB distance function
- Vector store add records support
- Vector similarity query helper
- Vector store input validation
- Mocked vector store tests
- Ingestion preview to vector store orchestration
- Chunk text embedding step
- Chunk record storage step
- Ingestion storage result model
- Zero-chunk handling
- Mocked ingestion-to-vector-store tests
- Query embedding flow
- Vector store similarity query flow
- Retrieved chunk model
- Retrieval metadata preservation
- Retrieval top_k support
- Retrieval where-filter pass-through
- Mocked retriever tests
- Arabic tutor prompt builder
- Retrieved context formatting
- Source metadata extraction
- Fallback/no-context behavior
- Prompt builder tests
- Ollama chat client foundation
- LLM service abstraction
- RAG answer result model
- Retriever to prompt builder to LLM orchestration
- RAG source preservation
- Mocked LLM and RAG orchestration tests
- `/api/v1/chat/ask`
- Chat request/response schemas
- RAG service dependency injection
- Endpoint tests with mocked RAG service
- Basic error handling
- Manual smoke test script
- Real PDF ingestion path
- Real embedding call path
- Real ChromaDB storage path
- Real RAG answer path
- CLI configuration overrides
- Improved source citation prompt rules
- Concise real RAG smoke test output
- Real RAG smoke test verbose mode
- Retrieved chunk preview cleanup
- README update

## Not Implemented Yet
- OCR
- Real admin upload endpoint
- Automatic real book ingestion
- Document ID generation strategy
- Google embedding provider
- Authentication
- Chat history
- Ollama generation
- Real frontend/backend integration
- Student personalization
- Advanced conversation memory
- Exam generation
- Answer evaluation

## Modified Files
- `app/api/health_routes.py`
- `app/api/chat_routes.py`
- `app/schemas/chat_schema.py`
- `app/dependencies.py`
- `app/main.py`
- `scripts/smoke_test_real_rag.py`
- `docker-compose.yml`
- `app/services/llm/ollama_client.py`
- `app/services/ingestion/pdf_extractor.py`
- `app/services/ingestion/text_cleaner.py`
- `app/services/ingestion/chunker.py`
- `app/services/ingestion/metadata_builder.py`
- `app/services/ingestion/ingestion_service.py`
- `app/services/embeddings/embedding_client.py`
- `app/services/embeddings/embedding_service.py`
- `app/services/vector_store/chroma_client.py`
- `app/services/vector_store/vector_store_service.py`
- `app/services/rag/retriever.py`
- `app/services/rag/prompt_builder.py`
- `app/services/rag/rag_service.py`
- `app/services/llm/llm_service.py`
- `app/prompts/arabic_tutor_prompt.txt`
- `app/config.py`
- `tests/test_llm_service.py`
- `tests/test_rag_service.py`
- `tests/test_chat_routes.py`
- `tests/test_dependency_health.py`
- `tests/test_pdf_extractor.py`
- `tests/test_text_cleaner.py`
- `tests/test_chunker.py`
- `tests/test_metadata_builder.py`
- `tests/test_ingestion_service.py`
- `tests/test_ingestion_to_vector_store.py`
- `tests/test_embedding_service.py`
- `tests/test_vector_store_service.py`
- `tests/test_retriever.py`
- `tests/test_prompt_builder.py`
- `README.md`
- `PROJECT_STATUS.md`
- `.env.example`
- `.gitignore`

## How to Run With Docker
docker compose up --build

## How to Run Locally
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

## How to Test
curl http://localhost:8001/health
curl http://localhost:8001/health/dependencies
pytest tests/test_pdf_extractor.py -v
pytest tests/test_text_cleaner.py -v
pytest tests/test_chunker.py -v
pytest tests/test_metadata_builder.py -v
pytest tests/test_ingestion_service.py -v
pytest tests/test_ingestion_to_vector_store.py -v
pytest tests/test_embedding_service.py -v
pytest tests/test_vector_store_service.py -v
pytest tests/test_retriever.py -v
pytest tests/test_prompt_builder.py -v
pytest tests/test_llm_service.py -v
pytest tests/test_rag_service.py -v
pytest tests/test_chat_routes.py -v
pytest tests/test_prompt_builder.py -v

## Known Issues
- Ollama models are not auto-pulled yet.
- `/health/dependencies` checks connectivity only; it does not validate model availability or AI behavior.
- OCR is not implemented yet; scanned/image-only PDFs may return empty page text.
- Semantic chunking is not implemented yet.
- Document IDs are not generated automatically yet.
- Ingestion-to-vector-store orchestration is not exposed through an API endpoint yet.
- Automatic real book ingestion is not implemented yet.
- Authentication is not implemented yet.
- Chat history is not implemented yet.
- Production admin ingestion endpoint is not implemented yet.
- Automatic large book ingestion is not implemented yet.
- Real Ollama Cloud requires `OLLAMA_API_KEY` in local `.env`.
- Vector store tests use mocks and do not require a real ChromaDB container.
- Ingestion-to-vector-store tests use mocks and do not require real Ollama or ChromaDB.
- Retriever tests use mocks and do not require real Ollama or ChromaDB.
- Prompt builder tests are deterministic and do not call an LLM.
- LLM and RAG service tests use mocks and do not call real Ollama or ChromaDB.
- Chat endpoint tests use mocked RAG service.
- Real RAG smoke test script is manual and is not part of pytest.
- Google embedding provider is not implemented yet.

## Next Recommended Step
Milestone 5A - Admin PDF Ingestion API
- Implement `POST /api/v1/ingest/pdf`
- Accept PDF + metadata
- Run ingestion to vector store
- Return ingestion summary
- Add endpoint tests with mocked services
