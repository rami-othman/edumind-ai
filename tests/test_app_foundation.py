from fastapi.testclient import TestClient

from app.main import app


def test_root_endpoint_returns_service_message() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "EduMind AI Service is running"}


def test_health_endpoint_returns_service_status() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "EduMind AI Service",
        "environment": "development",
        "version": "0.1.0",
    }
