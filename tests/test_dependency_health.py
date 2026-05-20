from fastapi.testclient import TestClient

from app.api import health_routes
from app.main import app


def test_dependency_health_returns_ok_when_dependencies_are_reachable(monkeypatch) -> None:
    def mock_chroma_health(*, host: str, port: int) -> dict[str, str]:
        return {"status": "ok", "url": f"http://{host}:{port}"}

    def mock_ollama_health(*, base_url: str) -> dict[str, str]:
        return {"status": "ok", "url": base_url}

    monkeypatch.setattr(health_routes, "check_chroma_health", mock_chroma_health)
    monkeypatch.setattr(health_routes, "check_ollama_health", mock_ollama_health)

    client = TestClient(app)

    response = client.get("/health/dependencies")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "EduMind AI Service",
        "dependencies": {
            "chroma": {
                "status": "ok",
                "url": "http://chroma:8000",
            },
            "ollama": {
                "status": "ok",
                "url": "http://ollama:11434",
            },
        },
    }


def test_dependency_health_returns_degraded_when_dependency_fails(monkeypatch) -> None:
    def mock_chroma_health(*, host: str, port: int) -> dict[str, str]:
        return {
            "status": "error",
            "url": f"http://{host}:{port}",
            "message": "Connection refused",
        }

    def mock_ollama_health(*, base_url: str) -> dict[str, str]:
        return {"status": "ok", "url": base_url}

    monkeypatch.setattr(health_routes, "check_chroma_health", mock_chroma_health)
    monkeypatch.setattr(health_routes, "check_ollama_health", mock_ollama_health)

    client = TestClient(app)

    response = client.get("/health/dependencies")

    assert response.status_code == 200
    assert response.json() == {
        "status": "degraded",
        "service": "EduMind AI Service",
        "dependencies": {
            "chroma": {
                "status": "error",
                "url": "http://chroma:8000",
                "message": "Connection refused",
            },
            "ollama": {
                "status": "ok",
                "url": "http://ollama:11434",
            },
        },
    }
