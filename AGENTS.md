# AGENTS.md — EduMind AI Service

## Project Name

EduMind AI

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

## Current Scope

The current development phase is the AI MVP foundation.

Build only the first clean architecture needed for:

1. Dockerized FastAPI AI service.
2. Dockerized ChromaDB.
3. Dockerized Ollama.
4. PDF ingestion pipeline.
5. RAG question-answering endpoint.
6. Arabic answer generation.
7. Source metadata support.

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

- Python 3.11+
- FastAPI
- Pydantic
- ChromaDB
- Ollama
- PyMuPDF for PDF extraction
- Docker
- Docker Compose

Preferred architecture:

- FastAPI handles API routes.
- ChromaDB stores document chunks and embeddings.
- Ollama runs the local LLM and embedding models.
- The Laravel/main backend will later communicate with this AI service through HTTP APIs.

---

## Docker-First Rule

The project must be designed to run with Docker from the beginning.

Expected services:

- ai-service
- chroma
- ollama

The service should run using:

```bash
docker compose up --build
```
