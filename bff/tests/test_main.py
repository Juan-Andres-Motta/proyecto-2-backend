from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_read_root():
    response = client.get("/bff/")
    assert response.status_code == 200
    assert response.json() == {"name": "BFF Service"}


def test_read_health():
    response = client.get("/bff/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
