from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "QELVORI" in response.text


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "running",
        "application": "QELVORI AI Research Intelligence",
        "version": "3.0.0"
    }


def test_api_documentation():
    response = client.get("/docs")

    assert response.status_code == 200
