from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_openapi_endpoint():
    """Test that OpenAPI spec is available"""
    response = client.get("/bff/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "paths" in data
