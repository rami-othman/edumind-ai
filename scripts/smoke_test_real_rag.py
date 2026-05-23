"""Manual smoke test for the real EduMind RAG pipeline.

This script is intentionally not part of pytest. It calls real services.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings  # noqa: E402
from app.services.embeddings.embedding_client import OllamaEmbeddingClient  # noqa: E402
from app.services.ingestion.ingestion_service import ingest_pdf_to_vector_store  # noqa: E402
from app.services.ingestion.metadata_builder import DocumentMetadata  # noqa: E402
from app.services.llm.ollama_client import OllamaChatClient, check_ollama_health  # noqa: E402
from app.services.rag.rag_service import answer_question_with_rag  # noqa: E402
from app.services.vector_store.chroma_client import ChromaClient  # noqa: E402


DEFAULT_PDF = "data/fake_pdfs/ohms_law_arabic.pdf"
DEFAULT_QUESTION = "ما هو قانون أوم؟"
DEFAULT_SUBJECT = "physics"
DEFAULT_GRADE = "12"
DEFAULT_UNIT = "electricity"
DEFAULT_LESSON = "ohms_law"
DEFAULT_SOURCE_TYPE = "smoke_test_sample"
DEFAULT_LANGUAGE = "arabic"


class SmokeTestError(Exception):
    """Raised when the smoke test cannot complete."""


class EmbeddingServiceAdapter:
    def __init__(self, client: OllamaEmbeddingClient) -> None:
        self.client = client

    def embed_text(self, text: str) -> list[float]:
        return self.client.embed_text(text)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return self.client.embed_texts(texts)


class LLMServiceAdapter:
    def __init__(self, client: OllamaChatClient) -> None:
        self.client = client

    def generate_answer(self, system_prompt: str, user_prompt: str) -> str:
        return self.client.generate(system_prompt, user_prompt)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a real RAG smoke test against ChromaDB, Ollama embeddings, and an Ollama LLM.",
    )
    parser.add_argument("--pdf", default=DEFAULT_PDF)
    parser.add_argument("--question", default=DEFAULT_QUESTION)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--subject", default=DEFAULT_SUBJECT)
    parser.add_argument("--grade", default=DEFAULT_GRADE)
    parser.add_argument("--unit", default=DEFAULT_UNIT)
    parser.add_argument("--lesson", default=DEFAULT_LESSON)
    parser.add_argument("--document-id", default=None)
    parser.add_argument("--chroma-host", default=None)
    parser.add_argument("--chroma-port", type=int, default=None)
    parser.add_argument("--embedding-base-url", default=None)
    parser.add_argument("--llm-base-url", default=None)
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print full source JSON and retrieved chunk metadata.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        run_smoke_test(args)
    except SmokeTestError as exc:
        print(f"Smoke test failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - manual safety net.
        print(f"Unexpected smoke test failure: {exc}", file=sys.stderr)
        return 1

    return 0


def run_smoke_test(args: argparse.Namespace) -> None:
    settings = get_settings()
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise SmokeTestError(f"PDF file does not exist: {pdf_path}")

    if args.top_k <= 0:
        raise SmokeTestError("--top-k must be greater than 0")

    document_id = args.document_id or _build_document_id()
    embedding_base_url = args.embedding_base_url or (
        settings.ollama_embedding_base_url or settings.ollama_base_url
    )
    llm_base_url = args.llm_base_url or (
        settings.ollama_llm_base_url or settings.ollama_base_url
    )
    chroma_host = args.chroma_host or settings.chroma_host
    chroma_port = args.chroma_port or settings.chroma_port

    if _requires_ollama_cloud_key(llm_base_url) and not settings.ollama_api_key:
        raise SmokeTestError(
            "OLLAMA_API_KEY is required in local .env when using Ollama Cloud.",
        )

    _verify_embedding_endpoint(embedding_base_url)

    vector_store_client = ChromaClient(
        host=chroma_host,
        port=chroma_port,
        collection_name=settings.chroma_collection_name,
        distance_function=settings.chroma_distance_function,
    )
    _verify_chroma(vector_store_client, chroma_host, chroma_port)

    embedding_service = EmbeddingServiceAdapter(
        OllamaEmbeddingClient(
            base_url=embedding_base_url,
            model=settings.ollama_embedding_model,
        ),
    )
    llm_service = LLMServiceAdapter(
        OllamaChatClient(
            base_url=llm_base_url,
            model=settings.ollama_llm_model,
            api_key=settings.ollama_api_key,
        ),
    )

    document_metadata = DocumentMetadata(
        document_id=document_id,
        file_name=pdf_path.name,
        source_path=str(pdf_path),
        grade=args.grade,
        subject=args.subject,
        unit=args.unit,
        lesson=args.lesson,
        source_type=DEFAULT_SOURCE_TYPE,
        language=DEFAULT_LANGUAGE,
    )

    print("Running real RAG smoke test...")
    print(f"PDF: {pdf_path}")
    print(f"Document ID: {document_id}")

    try:
        ingestion_result = ingest_pdf_to_vector_store(
            file_path=pdf_path,
            document_metadata=document_metadata,
            embedding_service=embedding_service,
            vector_store_client=vector_store_client,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
    except Exception as exc:
        raise SmokeTestError(f"PDF ingestion/vector storage failed: {exc}") from exc

    _print_ingestion_summary(ingestion_result)

    try:
        rag_answer = answer_question_with_rag(
            question=args.question,
            embedding_service=embedding_service,
            vector_store_client=vector_store_client,
            llm_service=llm_service,
            top_k=args.top_k,
            where={"document_id": document_id},
        )
    except Exception as exc:
        raise SmokeTestError(f"RAG answer generation failed: {exc}") from exc

    _print_rag_answer(rag_answer, verbose=args.verbose)


def _build_document_id() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"smoke_ohms_law_{timestamp}"


def _requires_ollama_cloud_key(base_url: str) -> bool:
    return base_url.rstrip("/").lower() == "https://ollama.com"


def _verify_embedding_endpoint(base_url: str) -> None:
    status = check_ollama_health(base_url=base_url)
    if status["status"] != "ok":
        raise SmokeTestError(
            f"Ollama embedding endpoint is unreachable at {base_url}: {status.get('message')}",
        )


def _verify_chroma(client: ChromaClient, host: str, port: int) -> None:
    try:
        client.heartbeat()
    except Exception as exc:
        raise SmokeTestError(f"ChromaDB is unreachable at {host}:{port}: {exc}") from exc


def _print_ingestion_summary(ingestion_result) -> None:
    _print_section("Ingestion Summary")
    print(f"Document ID: {ingestion_result.document_id}")
    print(f"Page count: {ingestion_result.page_count}")
    print(f"Total chunks: {ingestion_result.total_chunks}")
    print(f"Stored chunks: {ingestion_result.stored_chunks}")
    print(f"Empty pages: {ingestion_result.empty_pages}")


def _print_rag_answer(rag_answer, *, verbose: bool) -> None:
    _print_section("Answer")
    print(rag_answer.answer)

    _print_section("Sources")
    if rag_answer.sources:
        for index, source in enumerate(rag_answer.sources, start=1):
            print(_format_source_line(index, source))
    else:
        print("No sources returned.")

    if verbose:
        print("\nFull source JSON:")
        print(json.dumps(rag_answer.sources, ensure_ascii=False, indent=2))

    _print_section("Retrieved Chunks Preview")
    print(f"Count: {len(rag_answer.retrieved_chunks)}")
    for index, chunk in enumerate(rag_answer.retrieved_chunks, start=1):
        text = str(chunk.get("text", ""))
        print(f"\n[{index}] {chunk.get('chunk_id')}")
        print(preview_text(text))
        if verbose:
            print("Metadata:")
            print(json.dumps(chunk.get("metadata", {}), ensure_ascii=False, indent=2))


def _print_section(title: str) -> None:
    print(f"\n{title}")
    print("=" * len(title))


def _format_source_line(index: int, source: dict[str, object]) -> str:
    fields = [
        ("file", source.get("file_name")),
        ("page", source.get("page_number")),
        ("chunk", source.get("chunk_index")),
        ("subject", source.get("subject")),
        ("lesson", source.get("lesson")),
        ("distance", _format_distance(source.get("distance"))),
    ]
    details = [f"{label}={value}" for label, value in fields if value is not None]
    return f"[{index}] " + " | ".join(details)


def _format_distance(value: object) -> str | None:
    if isinstance(value, int | float) and not isinstance(value, bool):
        return f"{float(value):.4f}"

    return None


def preview_text(text: str, max_chars: int = 300) -> str:
    compact_text = re.sub(r"\s+", " ", text).strip()
    if len(compact_text) <= max_chars:
        return compact_text

    return f"{compact_text[:max_chars].rstrip()}..."


if __name__ == "__main__":
    raise SystemExit(main())
