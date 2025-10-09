import pytest


@pytest.fixture
def mock_settings(monkeypatch):
    """Fixture to provide mock settings for tests."""
    monkeypatch.setenv("CATALOG_URL", "http://test-catalog:8000")
    monkeypatch.setenv("CLIENT_URL", "http://test-client:8000")
    monkeypatch.setenv("DELIVERY_URL", "http://test-delivery:8000")
    monkeypatch.setenv("INVENTORY_URL", "http://test-inventory:8000")
    monkeypatch.setenv("ORDER_URL", "http://test-order:8000")
    monkeypatch.setenv("SELLER_URL", "http://test-seller:8000")
    monkeypatch.setenv("SERVICE_TIMEOUT", "5.0")


@pytest.fixture
def sample_provider_data():
    """Fixture providing sample provider data."""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "test provider",
        "nit": "123456789",
        "contact_name": "john doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "address": "123 test st",
        "country": "US",
        "created_at": "2025-01-15T10:30:00Z",
        "updated_at": "2025-01-15T10:30:00Z",
    }


@pytest.fixture
def sample_product_data():
    """Fixture providing sample product data."""
    return {
        "id": "660e8400-e29b-41d4-a716-446655440000",
        "provider_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "test product",
        "category": "electronics",
        "description": "test description",
        "price": "99.99",
        "status": "active",
        "created_at": "2025-01-15T10:30:00Z",
        "updated_at": "2025-01-15T10:30:00Z",
    }


@pytest.fixture
def sample_catalog_response(sample_provider_data, sample_product_data):
    """Fixture providing sample catalog response."""
    return {
        "providers": [sample_provider_data],
        "products": [sample_product_data],
    }
