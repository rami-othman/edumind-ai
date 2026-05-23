# PROJECT_STATUS.md - EduMind AI Service

## Current Milestone
Milestone 4B - RAG Prompt Builder

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
- README update

## Not Implemented Yet
- OCR
- Real admin upload endpoint
- Automatic real book ingestion
- Document ID generation strategy
- Google embedding provider
- RAG orchestration
- Chat endpoint logic
- LLM answer generation
- Ollama generation
- RAG
- Exam generation
- Answer evaluation

## Modified Files
- `app/api/health_routes.py`
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
- `app/prompts/arabic_tutor_prompt.txt`
- `app/config.py`
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

## Known Issues
- Ollama models are not auto-pulled yet.
- `/health/dependencies` checks connectivity only; it does not validate model availability or AI behavior.
- OCR is not implemented yet; scanned/image-only PDFs may return empty page text.
- Semantic chunking is not implemented yet.
- Document IDs are not generated automatically yet.
- Ingestion-to-vector-store orchestration is not exposed through an API endpoint yet.
- Automatic real book ingestion is not implemented yet.
- RAG answer generation is not implemented yet.
- RAG service orchestration is not implemented yet.
- Chat endpoint is not connected yet.
- Vector store tests use mocks and do not require a real ChromaDB container.
- Ingestion-to-vector-store tests use mocks and do not require real Ollama or ChromaDB.
- Retriever tests use mocks and do not require real Ollama or ChromaDB.
- Prompt builder tests are deterministic and do not call an LLM.
- Google embedding provider is not implemented yet.

## Next Recommended Step
Milestone 4C - RAG Service Orchestration
- Connect retriever -> prompt builder -> LLM service
- Return answer + sources
- Add mocked tests
