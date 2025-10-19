from fastapi.testclient import TestClient
from ..app import app

client = TestClient(app)


def test_read_root():
    response = client.get("/client")
    assert response.status_code == 200
    assert response.json() == {"name": "Client Service"}


def test_read_health():
    response = client.get("/client/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
