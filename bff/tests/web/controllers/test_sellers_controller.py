"""Unit tests for sellers controller."""
from unittest.mock import AsyncMock, Mock
from uuid import UUID
import pytest
from fastapi import HTTPException
from web.ports.seller_port import SellerPort
from web.controllers.sellers_controller import create_seller, get_sellers, get_seller_sales_plans
from web.schemas.seller_schemas import SellerCreate, SellerCreateResponse

@pytest.fixture
def mock_seller_port():
    return Mock(spec=SellerPort)

@pytest.fixture
def mock_web_user():
    """Mock web admin user for authorization tests."""
    return {
        "sub": "web-admin-cognito-id-123",
        "email": "admin@medisupply.com",
        "cognito:groups": ["web_users"],
    }

class TestSellersController:
    @pytest.mark.asyncio
    async def test_create_seller(self, mock_seller_port):
        """Test basic seller creation through controller."""
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
    async def test_create_seller_end_to_end_success(self, mock_seller_port, mock_web_user):
        """Test successful end-to-end seller creation with saga pattern."""
        seller_data = SellerCreate(
            name="Test Seller",
            email="seller@example.com",
            phone="+1234567890",
            city="Miami",
            country="United States"
        )

        # Mock successful saga response
        mock_response = SellerCreateResponse(
            id="seller-uuid-456",
            message="Seller created successfully"
        )
        mock_seller_port.create_seller = AsyncMock(return_value=mock_response)

        # Execute controller
        result = await create_seller(
            seller=seller_data,
            seller_port=mock_seller_port,
            user=mock_web_user
        )

        # Verify port was called with correct data
        mock_seller_port.create_seller.assert_called_once_with(seller_data)

        # Verify response
        assert result.id == "seller-uuid-456"
        assert result.message == "Seller created successfully"

    @pytest.mark.asyncio
    async def test_create_seller_saga_cognito_failure(self, mock_seller_port, mock_web_user):
        """Test seller creation when Cognito step fails."""
        seller_data = SellerCreate(
            name="Test Seller",
            email="existing@example.com",
            phone="+1234567890",
            city="Miami",
            country="United States"
        )

        # Mock Cognito failure in saga
        mock_seller_port.create_seller = AsyncMock(
            side_effect=HTTPException(
                status_code=500,
                detail="Failed to create seller authentication: User already exists"
            )
        )

        # Execute controller and expect exception
        with pytest.raises(HTTPException) as exc_info:
            await create_seller(
                seller=seller_data,
                seller_port=mock_seller_port,
                user=mock_web_user
            )

        assert exc_info.value.status_code == 500
        assert "Failed to create seller authentication" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_seller_saga_microservice_failure(self, mock_seller_port, mock_web_user):
        """Test seller creation when seller microservice fails (triggers rollback)."""
        seller_data = SellerCreate(
            name="Test Seller",
            email="test@example.com",
            phone="+1234567890",
            city="Miami",
            country="United States"
        )

        # Mock seller microservice failure (after Cognito success, triggers rollback)
        mock_seller_port.create_seller = AsyncMock(
            side_effect=HTTPException(
                status_code=500,
                detail="Failed to complete seller creation. Please try again."
            )
        )

        # Execute controller and expect exception
        with pytest.raises(HTTPException) as exc_info:
            await create_seller(
                seller=seller_data,
                seller_port=mock_seller_port,
                user=mock_web_user
            )

        assert exc_info.value.status_code == 500
        assert "Failed to complete seller creation" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_sellers(self, mock_seller_port):
        """Test getting sellers list."""
        mock_seller_port.get_sellers = AsyncMock(return_value={"items": []})
        result = await get_sellers(seller_port=mock_seller_port)
        mock_seller_port.get_sellers.assert_called_once()
        assert result == {"items": []}
