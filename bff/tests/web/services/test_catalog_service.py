from unittest.mock import AsyncMock, patch

import httpx
import pytest

from web.services.catalog_service import CatalogService


@pytest.mark.asyncio
async def test_get_providers_success():
    """Test successful provider retrieval."""
    service = CatalogService()

    mock_response = {
        "items": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "test provider",
                "nit": "123456789",
            }
        ],
        "total": 1,
        "page": 1,
        "size": 1,
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response,
        )
        mock_get.return_value.raise_for_status = lambda: None

        result = await service.get_providers(limit=10, offset=0)

        assert result == mock_response
        assert len(result["items"]) == 1


@pytest.mark.asyncio
async def test_get_products_success():
    """Test successful product retrieval."""
    service = CatalogService()

    mock_response = {
        "items": [
            {
                "id": "660e8400-e29b-41d4-a716-446655440000",
                "provider_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "test product",
                "price": "99.99",
            }
        ],
        "total": 1,
        "page": 1,
        "size": 1,
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response,
        )
        mock_get.return_value.raise_for_status = lambda: None

        result = await service.get_products(limit=10, offset=0)

        assert result == mock_response
        assert len(result["items"]) == 1


@pytest.mark.asyncio
async def test_get_providers_http_error():
    """Test provider retrieval with HTTP error."""
    service = CatalogService()

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock(status_code=500)

        def raise_error():
            raise httpx.HTTPStatusError(
                "Internal Server Error",
                request=AsyncMock(),
                response=AsyncMock(status_code=500),
            )

        mock_response.raise_for_status = raise_error
        mock_get.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            await service.get_providers()


@pytest.mark.asyncio
async def test_get_providers_with_pagination():
    """Test provider retrieval with custom pagination."""
    service = CatalogService()

    mock_response = {"items": [], "total": 0}

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response,
        )
        mock_get.return_value.raise_for_status = lambda: None

        result = await service.get_providers(limit=5, offset=10)

        # Verify the correct parameters were passed
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args.kwargs["params"]["limit"] == 5
        assert call_args.kwargs["params"]["offset"] == 10


@pytest.mark.asyncio
async def test_create_provider_success():
    """Test successful provider creation."""
    service = CatalogService()

    provider_data = {
        "name": "Test Provider",
        "nit": "123456789",
        "contact_name": "John Doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "address": "123 Test St",
        "country": "United States",
    }

    mock_response = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "message": "Provider created successfully",
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=201,
            json=lambda: mock_response,
        )
        mock_post.return_value.raise_for_status = lambda: None

        result = await service.create_provider(provider_data)

        assert result == mock_response
        assert "id" in result
        assert result["message"] == "Provider created successfully"
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_create_provider_http_error():
    """Test provider creation with HTTP error."""
    service = CatalogService()

    provider_data = {
        "name": "Test Provider",
        "nit": "123456789",
        "contact_name": "John Doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "address": "123 Test St",
        "country": "United States",
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = AsyncMock(status_code=500)

        def raise_error():
            raise httpx.HTTPStatusError(
                "Internal Server Error",
                request=AsyncMock(),
                response=AsyncMock(status_code=500),
            )

        mock_response.raise_for_status = raise_error
        mock_post.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            await service.create_provider(provider_data)


@pytest.mark.asyncio
async def test_create_products_success():
    """Test successful batch product creation."""
    service = CatalogService()

    products_data = [
        {
            "provider_id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Product 1",
            "category": "SPECIAL_MEDICATIONS",
            "description": "Description 1",
            "price": "100.00",
        },
        {
            "provider_id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Product 2",
            "category": "SURGICAL_SUPPLIES",
            "description": "Description 2",
            "price": "200.00",
        },
    ]

    mock_response = {
        "created": [
            {
                "id": "660e8400-e29b-41d4-a716-446655440000",
                "provider_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Product 1",
                "category": "SPECIAL_MEDICATIONS",
                "description": "Description 1",
                "price": "100.00",
                "status": "PENDING_APPROVAL",
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T10:30:00Z",
            },
            {
                "id": "770e8400-e29b-41d4-a716-446655440000",
                "provider_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Product 2",
                "category": "SURGICAL_SUPPLIES",
                "description": "Description 2",
                "price": "200.00",
                "status": "PENDING_APPROVAL",
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T10:30:00Z",
            },
        ],
        "count": 2,
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=201,
            json=lambda: mock_response,
        )
        mock_post.return_value.raise_for_status = lambda: None

        result = await service.create_products(products_data)

        assert result == mock_response
        assert "created" in result
        assert "count" in result
        assert len(result["created"]) == 2
        assert result["count"] == 2
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_create_products_http_error():
    """Test batch product creation with HTTP error."""
    service = CatalogService()

    products_data = [
        {
            "provider_id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Product 1",
            "category": "SPECIAL_MEDICATIONS",
            "description": "Description 1",
            "price": "100.00",
        },
    ]

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = AsyncMock(status_code=500)

        def raise_error():
            raise httpx.HTTPStatusError(
                "Internal Server Error",
                request=AsyncMock(),
                response=AsyncMock(status_code=500),
            )

        mock_response.raise_for_status = raise_error
        mock_post.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            await service.create_products(products_data)
