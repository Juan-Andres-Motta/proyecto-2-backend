from datetime import datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_order(async_client: AsyncClient):
    """Test creating an order through the API."""
    order_data = {
        "client_id": "550e8400-e29b-41d4-a716-446655440000",
        "seller_id": "550e8400-e29b-41d4-a716-446655440001",
        "deliver_id": "550e8400-e29b-41d4-a716-446655440002",
        "route_id": "550e8400-e29b-41d4-a716-446655440003",
        "order_date": "2025-10-09T12:00:00Z",
        "destination_address": "123 Main St, City, Country",
        "creation_method": "web_client",
        "items": [
            {
                "product_id": "550e8400-e29b-41d4-a716-446655440004",
                "inventory_id": "550e8400-e29b-41d4-a716-446655440005",
                "quantity": 2,
                "unit_price": 29.99,
            },
            {
                "product_id": "550e8400-e29b-41d4-a716-446655440006",
                "inventory_id": "550e8400-e29b-41d4-a716-446655440007",
                "quantity": 1,
                "unit_price": 15.50,
            },
        ],
    }

    response = await async_client.post("/order", json=order_data)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["message"] == "Order created successfully"


@pytest.mark.asyncio
async def test_create_order_with_single_item(async_client: AsyncClient):
    """Test creating an order with a single item."""
    order_data = {
        "client_id": "550e8400-e29b-41d4-a716-446655440010",
        "seller_id": "550e8400-e29b-41d4-a716-446655440011",
        "deliver_id": "550e8400-e29b-41d4-a716-446655440012",
        "route_id": "550e8400-e29b-41d4-a716-446655440013",
        "order_date": "2025-10-10T14:30:00Z",
        "destination_address": "456 Test Ave",
        "creation_method": "mobile_client",
        "items": [
            {
                "product_id": "550e8400-e29b-41d4-a716-446655440014",
                "inventory_id": "550e8400-e29b-41d4-a716-446655440015",
                "quantity": 5,
                "unit_price": 12.75,
            }
        ],
    }

    response = await async_client.post("/order", json=order_data)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["message"] == "Order created successfully"


@pytest.mark.asyncio
async def test_create_order_validation_error(async_client: AsyncClient):
    """Test creating an order with invalid data."""
    # Missing required field 'items'
    order_data = {
        "client_id": "550e8400-e29b-41d4-a716-446655440020",
        "seller_id": "550e8400-e29b-41d4-a716-446655440021",
        "deliver_id": "550e8400-e29b-41d4-a716-446655440022",
        "route_id": "550e8400-e29b-41d4-a716-446655440023",
        "order_date": "2025-10-11T10:00:00Z",
        "destination_address": "789 Sample Blvd",
        "creation_method": "portal_client",
    }

    response = await async_client.post("/order", json=order_data)

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_list_orders_empty(async_client: AsyncClient):
    """Test listing orders when database is empty."""
    response = await async_client.get("/orders")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) == 0
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["size"] == 0
    assert data["has_next"] is False
    assert data["has_previous"] is False


@pytest.mark.asyncio
async def test_list_orders_with_data(async_client: AsyncClient):
    """Test listing orders with data."""
    # Create an order first
    order_data = {
        "client_id": "550e8400-e29b-41d4-a716-446655440030",
        "seller_id": "550e8400-e29b-41d4-a716-446655440031",
        "deliver_id": "550e8400-e29b-41d4-a716-446655440032",
        "route_id": "550e8400-e29b-41d4-a716-446655440033",
        "order_date": "2025-10-12T09:00:00Z",
        "destination_address": "321 Order St",
        "creation_method": "web_client",
        "items": [
            {
                "product_id": "550e8400-e29b-41d4-a716-446655440034",
                "inventory_id": "550e8400-e29b-41d4-a716-446655440035",
                "quantity": 3,
                "unit_price": 20.00,
            }
        ],
    }
    await async_client.post("/order", json=order_data)

    # List orders
    response = await async_client.get("/orders")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["total"] == 1
    assert "id" in data["items"][0]
    assert "client_id" in data["items"][0]
    assert "items" in data["items"][0]
    assert len(data["items"][0]["items"]) == 1


@pytest.mark.asyncio
async def test_list_orders_pagination(async_client: AsyncClient):
    """Test listing orders with pagination."""
    # Create multiple orders
    for i in range(5):
        order_data = {
            "client_id": f"550e8400-e29b-41d4-a716-44665544{i:04d}",
            "seller_id": f"550e8400-e29b-41d4-a716-44665545{i:04d}",
            "deliver_id": f"550e8400-e29b-41d4-a716-44665546{i:04d}",
            "route_id": f"550e8400-e29b-41d4-a716-44665547{i:04d}",
            "order_date": "2025-10-13T10:00:00Z",
            "destination_address": f"{i} Pagination Ave",
            "creation_method": "web_client",
            "items": [
                {
                    "product_id": f"550e8400-e29b-41d4-a716-44665548{i:04d}",
                    "inventory_id": f"550e8400-e29b-41d4-a716-44665549{i:04d}",
                    "quantity": 1,
                    "unit_price": 10.00,
                }
            ],
        }
        await async_client.post("/order", json=order_data)

    # Get first page
    response = await async_client.get("/orders?limit=2&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["has_next"] is True
    assert data["has_previous"] is False

    # Get second page
    response = await async_client.get("/orders?limit=2&offset=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["page"] == 2
    assert data["has_next"] is True
    assert data["has_previous"] is True


@pytest.mark.asyncio
async def test_list_orders_validation(async_client: AsyncClient):
    """Test list orders endpoint parameter validation."""
    # Test limit too high
    response = await async_client.get("/orders?limit=101")
    assert response.status_code == 422

    # Test limit too low
    response = await async_client.get("/orders?limit=0")
    assert response.status_code == 422

    # Test negative offset
    response = await async_client.get("/orders?offset=-1")
    assert response.status_code == 422
