"""Unit tests for sellers controller."""
from unittest.mock import AsyncMock, Mock
from uuid import UUID
import pytest
from web.ports.seller_port import SellerPort
from web.controllers.sellers_controller import create_seller, get_sellers, get_seller_sales_plans
from web.schemas.seller_schemas import SellerCreate

@pytest.fixture
def mock_seller_port():
    return Mock(spec=SellerPort)

class TestSellersController:
    @pytest.mark.asyncio
    async def test_create_seller(self, mock_seller_port):
        seller_data = SellerCreate(
            name="Test Seller",
            email="test@test.com",
            phone="123456789",
            city="Test City",
            country="CO"
        )
        mock_seller_port.create_seller = AsyncMock(return_value={"id": "test-id", "message": "Created"})
        result = await create_seller(seller=seller_data, seller_port=mock_seller_port)
        mock_seller_port.create_seller.assert_called_once_with(seller_data)
        assert result == {"id": "test-id", "message": "Created"}

    @pytest.mark.asyncio
    async def test_get_sellers(self, mock_seller_port):
        mock_seller_port.get_sellers = AsyncMock(return_value={"items": []})
        result = await get_sellers(seller_port=mock_seller_port)
        mock_seller_port.get_sellers.assert_called_once()
        assert result == {"items": []}
