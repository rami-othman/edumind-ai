from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def parse_env(relative_path: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in read_text(relative_path).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, value = stripped.split("=", 1)
        values[key] = value
    return values


def test_dockerfile_runs_fastapi_through_entrypoint() -> None:
    dockerfile = read_text("docker/Dockerfile")

    assert "FROM python:3.11-slim" in dockerfile
    assert "WORKDIR /app" in dockerfile
    assert "COPY requirements.txt" in dockerfile
    assert "pip install" in dockerfile
    assert "COPY . ." in dockerfile
    assert "EXPOSE 8001" in dockerfile
    assert 'ENTRYPOINT ["docker/entrypoint.sh"]' in dockerfile


def test_entrypoint_starts_uvicorn_without_reload() -> None:
    entrypoint = read_text("docker/entrypoint.sh")

    assert 'exec uvicorn app.main:app --host "${APP_HOST:-0.0.0.0}" --port "${APP_PORT:-8001}"' in entrypoint
    assert "--reload" not in entrypoint


def test_compose_defines_required_services_and_volumes() -> None:
    compose = yaml.safe_load(read_text("docker-compose.yml"))

    assert set(compose["services"]) == {"ai-service", "chroma", "ollama"}

    ai_service = compose["services"]["ai-service"]
    assert ai_service["container_name"] == "edumind-ai-service"
    assert ai_service["build"]["dockerfile"] == "docker/Dockerfile"
    assert ai_service["env_file"] == [".env"]
    assert "8001:8001" in ai_service["ports"]
    assert "./app:/app/app" in ai_service["volumes"]
    assert "./data:/app/data" in ai_service["volumes"]
    assert set(ai_service["depends_on"]) == {"chroma", "ollama"}

    chroma = compose["services"]["chroma"]
    assert chroma["image"] == "chromadb/chroma:latest"
    assert chroma["container_name"] == "edumind-chroma"
    assert "8000:8000" in chroma["ports"]
    assert "chroma_data:/chroma/chroma" in chroma["volumes"]

    ollama = compose["services"]["ollama"]
    assert ollama["image"] == "ollama/ollama:latest"
    assert ollama["container_name"] == "edumind-ollama"
    assert "11434:11434" in ollama["ports"]
    assert "ollama_data:/root/.ollama" in ollama["volumes"]

    assert set(compose["volumes"]) == {"chroma_data", "ollama_data"}


def test_env_files_use_expected_milestone_variables() -> None:
    expected = {
        "APP_NAME": "EduMind AI Service",
        "APP_ENV": "development",
        "APP_HOST": "0.0.0.0",
        "APP_PORT": "8001",
        "CHROMA_HOST": "chroma",
        "CHROMA_PORT": "8000",
        "CHROMA_COLLECTION_NAME": "edumind_content",
        "OLLAMA_BASE_URL": "http://ollama:11434",
        "OLLAMA_LLM_MODEL": "gemma3:12b",
        "OLLAMA_EMBEDDING_MODEL": "nomic-embed-text",
        "UPLOAD_DIR": "/app/data/uploads",
        "PROCESSED_DIR": "/app/data/processed",
        "CHUNK_SIZE": "800",
        "CHUNK_OVERLAP": "150",
        "TOP_K": "5",
    }

    for env_file in (".env", ".env.example"):
        values = parse_env(env_file)
        assert values == expected
        assert "AI_SERVICE_HOST" not in values
        assert "AI_SERVICE_PORT" not in values
        assert "AI_SERVICE_ENV" not in values
