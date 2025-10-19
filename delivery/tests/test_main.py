from fastapi.testclient import TestClient
from ..app import app

client = TestClient(app)


def test_read_root():
    response = client.get("/delivery")
    assert response.status_code == 200
    assert response.json() == {"name": "Delivery Service"}


def test_read_health():
    response = client.get("/delivery/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
