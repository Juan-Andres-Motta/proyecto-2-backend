"""
Unit tests for SellerAdapter.

Tests OUR logic:
- Calling correct HTTP endpoints
- Saga pattern for seller creation with Cognito integration
"""

from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest
from fastapi import HTTPException

from web.adapters.seller_adapter import SellerAdapter
from web.adapters.http_client import HttpClient
from web.schemas.seller_schemas import SellerCreate, SalesPlanCreate
from common.auth.cognito_service import CognitoService


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    return Mock(spec=HttpClient)


@pytest.fixture
def mock_cognito_service():
    """Create a mock Cognito service."""
    return Mock(spec=CognitoService)


@pytest.fixture
def seller_adapter(mock_http_client, mock_cognito_service):
    """Create a seller adapter with mock HTTP client and Cognito service."""
    return SellerAdapter(mock_http_client, mock_cognito_service)


class TestSellerAdapterCreateSellerSaga:
    """Test create_seller saga pattern with Cognito integration."""

    @pytest.mark.asyncio
    async def test_create_seller_saga_success(self, seller_adapter, mock_http_client, mock_cognito_service):
        """Test successful saga: Cognito user created -> Seller created."""
        seller_data = SellerCreate(
            name="Test Seller",
            email="test@example.com",
            phone="+1234567890",
            city="Test City",
            country="CO",
        )

        # Mock Cognito service response (Step 1)
        mock_cognito_service.create_user = AsyncMock(
            return_value={
                "user_id": "cognito-user-id-123",
                "username": "test@example.com"
            }
        )

        # Mock seller microservice response (Step 2)
        mock_http_client.post = AsyncMock(
            return_value={"id": "seller-id-456", "message": "Seller created successfully"}
        )

        # Execute saga
        result = await seller_adapter.create_seller(seller_data)

        # Verify Step 1: Cognito user creation called with correct params
        mock_cognito_service.create_user.assert_called_once_with(
            email="test@example.com",
            password="TestSeller@Password123",
            name="Test Seller",
            user_type="seller"
        )

        # Verify Step 2: Seller microservice called with cognito_user_id
        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert call_args.args[0] == "/seller/sellers"
        assert call_args.kwargs["json"]["cognito_user_id"] == "cognito-user-id-123"
        assert call_args.kwargs["json"]["email"] == "test@example.com"

        # Verify response
        assert result.id == "seller-id-456"
        assert result.message == "Seller created successfully"

    @pytest.mark.asyncio
    async def test_create_seller_cognito_failure(self, seller_adapter, mock_http_client, mock_cognito_service):
        """Test saga Step 1 failure: Cognito creation fails, no rollback needed."""
        seller_data = SellerCreate(
            name="Test Seller",
            email="test@example.com",
            phone="+1234567890",
            city="Test City",
            country="CO",
        )

        # Mock Cognito failure (Step 1)
        mock_cognito_service.create_user = AsyncMock(
            side_effect=Exception("Cognito error: User already exists")
        )

        # Execute saga - should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await seller_adapter.create_seller(seller_data)

        # Verify error response
        assert exc_info.value.status_code == 500
        assert "Failed to create seller authentication" in exc_info.value.detail

        # Verify Step 2 was never called
        mock_http_client.post.assert_not_called()

        # Verify no rollback was attempted (nothing to rollback)
        mock_cognito_service.delete_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_seller_microservice_failure_rollback_success(self, seller_adapter, mock_http_client, mock_cognito_service):
        """Test saga Step 2 failure with successful rollback: Seller creation fails, Cognito user deleted."""
        seller_data = SellerCreate(
            name="Test Seller",
            email="test@example.com",
            phone="+1234567890",
            city="Test City",
            country="CO",
        )

        # Mock Cognito success (Step 1)
        mock_cognito_service.create_user = AsyncMock(
            return_value={
                "user_id": "cognito-user-id-123",
                "username": "test@example.com"
            }
        )

        # Mock seller microservice failure (Step 2)
        mock_http_client.post = AsyncMock(
            side_effect=Exception("Seller service error: Database connection failed")
        )

        # Mock successful rollback
        mock_cognito_service.delete_user = AsyncMock()

        # Execute saga - should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await seller_adapter.create_seller(seller_data)

        # Verify error response
        assert exc_info.value.status_code == 500
        assert "Failed to complete seller creation" in exc_info.value.detail

        # Verify rollback was called
        mock_cognito_service.delete_user.assert_called_once_with("test@example.com")

    @pytest.mark.asyncio
    async def test_create_seller_microservice_failure_rollback_fails(self, seller_adapter, mock_http_client, mock_cognito_service):
        """Test worst case: Seller creation fails AND rollback fails (manual intervention required)."""
        seller_data = SellerCreate(
            name="Test Seller",
            email="test@example.com",
            phone="+1234567890",
            city="Test City",
            country="CO",
        )

        # Mock Cognito success (Step 1)
        mock_cognito_service.create_user = AsyncMock(
            return_value={
                "user_id": "cognito-user-id-123",
                "username": "test@example.com"
            }
        )

        # Mock seller microservice failure (Step 2)
        mock_http_client.post = AsyncMock(
            side_effect=Exception("Seller service error")
        )

        # Mock rollback failure
        mock_cognito_service.delete_user = AsyncMock(
            side_effect=Exception("Cognito delete failed")
        )

        # Execute saga - should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await seller_adapter.create_seller(seller_data)

        # Verify error response
        assert exc_info.value.status_code == 500
        assert "Failed to complete seller creation" in exc_info.value.detail

        # Verify rollback was attempted
        mock_cognito_service.delete_user.assert_called_once_with("test@example.com")

        # Note: In real scenario, this would log CRITICAL message for manual intervention

    @pytest.mark.asyncio
    async def test_create_seller_password_generation(self, seller_adapter, mock_http_client, mock_cognito_service):
        """Test password generation from various seller names."""
        test_cases = [
            ("John Doe", "JohnDoe@Password123"),
            ("María José", "MaraJos@Password123"),  # Accented chars removed by regex
            ("Test-Seller_123", "TestSeller123@Password123"),
            ("Seller@Company!", "SellerCompany@Password123"),
            ("Simple", "Simple@Password123"),
        ]

        for seller_name, expected_password in test_cases:
            seller_data = SellerCreate(
                name=seller_name,
                email="test@example.com",
                phone="+1234567890",
                city="Test City",
                country="CO",
            )

            # Mock Cognito success
            mock_cognito_service.create_user = AsyncMock(
                return_value={
                    "user_id": "cognito-user-id-123",
                    "username": "test@example.com"
                }
            )

            # Mock seller microservice success
            mock_http_client.post = AsyncMock(
                return_value={"id": "seller-id-456", "message": "Created"}
            )

            # Execute
            await seller_adapter.create_seller(seller_data)

            # Verify password generation
            call_args = mock_cognito_service.create_user.call_args
            assert call_args.kwargs["password"] == expected_password

            # Reset mocks for next iteration
            mock_cognito_service.create_user.reset_mock()
            mock_http_client.post.reset_mock()

    @pytest.mark.asyncio
    async def test_create_seller_cognito_user_id_added(self, seller_adapter, mock_http_client, mock_cognito_service):
        """Test that cognito_user_id is properly added to seller data before calling microservice."""
        seller_data = SellerCreate(
            name="Test Seller",
            email="test@example.com",
            phone="+1234567890",
            city="Test City",
            country="CO",
        )

        # Mock Cognito success with specific user_id
        mock_cognito_service.create_user = AsyncMock(
            return_value={
                "user_id": "unique-cognito-id-789",
                "username": "test@example.com"
            }
        )

        # Mock seller microservice success
        mock_http_client.post = AsyncMock(
            return_value={"id": "seller-id-456", "message": "Created"}
        )

        # Execute saga
        await seller_adapter.create_seller(seller_data)

        # Verify cognito_user_id was added to request payload
        call_args = mock_http_client.post.call_args
        request_payload = call_args.kwargs["json"]

        assert "cognito_user_id" in request_payload
        assert request_payload["cognito_user_id"] == "unique-cognito-id-789"

        # Verify all original seller data is preserved
        assert request_payload["name"] == "Test Seller"
        assert request_payload["email"] == "test@example.com"
        assert request_payload["phone"] == "+1234567890"
        assert request_payload["city"] == "Test City"
        assert request_payload["country"] == "CO"

    @pytest.mark.asyncio
    async def test_create_seller_group_assignment_success(self, seller_adapter, mock_http_client, mock_cognito_service):
        """Test that seller user is added to seller_users group."""
        seller_data = SellerCreate(
            name="Test Seller",
            email="test@example.com",
            phone="+1234567890",
            city="Test City",
            country="CO",
        )

        # Mock Cognito success
        mock_cognito_service.create_user = AsyncMock(
            return_value={
                "user_id": "cognito-user-id-123",
                "username": "test@example.com"
            }
        )

        # Mock add_user_to_group
        mock_cognito_service.add_user_to_group = AsyncMock()

        # Mock seller microservice success
        mock_http_client.post = AsyncMock(
            return_value={"id": "seller-id-456", "message": "Created"}
        )

        # Execute saga
        await seller_adapter.create_seller(seller_data)

        # Verify add_user_to_group was called with correct params
        mock_cognito_service.add_user_to_group.assert_called_once_with(
            username="test@example.com",
            group_name="seller_users"
        )

    @pytest.mark.asyncio
    async def test_create_seller_group_assignment_failure_triggers_rollback(self, seller_adapter, mock_http_client, mock_cognito_service):
        """Test saga Step 1.5 failure: Group assignment fails, Cognito user is deleted."""
        seller_data = SellerCreate(
            name="Test Seller",
            email="test@example.com",
            phone="+1234567890",
            city="Test City",
            country="CO",
        )

        # Mock Cognito success
        mock_cognito_service.create_user = AsyncMock(
            return_value={
                "user_id": "cognito-user-id-123",
                "username": "test@example.com"
            }
        )

        # Mock add_user_to_group failure
        mock_cognito_service.add_user_to_group = AsyncMock(
            side_effect=Exception("Failed to add user to group")
        )

        # Mock delete_user for rollback
        mock_cognito_service.delete_user = AsyncMock()

        # Execute saga - should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await seller_adapter.create_seller(seller_data)

        # Verify error response
        assert exc_info.value.status_code == 500
        assert "Failed to assign seller permissions" in exc_info.value.detail

        # Verify rollback was called
        mock_cognito_service.delete_user.assert_called_once_with("test@example.com")

        # Verify seller microservice was NOT called
        mock_http_client.post.assert_not_called()


class TestSellerAdapterGetSellers:
    """Test get_sellers calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, seller_adapter, mock_http_client):
        """Test that GET /sellers is called."""
        mock_http_client.get = AsyncMock(
            return_value={
                "items": [],
                "total": 0,
                "page": 1,
                "size": 10,
                "has_next": False,
                "has_previous": False,
            }
        )

        await seller_adapter.get_sellers()

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert call_args.args[0] == "/seller/sellers"


class TestSellerAdapterCreateSalesPlan:
    """Test create_sales_plan calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, seller_adapter, mock_http_client):
        """Test that POST /sales-plans is called and response is parsed correctly."""
        sales_plan_data = SalesPlanCreate(
            seller_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            sales_period="Q1-2025",
            goal=10000.0,
        )

        # Mock seller service response - returns full sales plan object
        mock_http_client.post = AsyncMock(
            return_value={
                "id": "test-id",
                "seller": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Test Seller",
                    "email": "test@example.com",
                    "phone": "1234567890",
                    "city": "Test City",
                    "country": "CO",
                    "created_at": "2025-10-18T00:00:00Z",
                    "updated_at": "2025-10-18T00:00:00Z"
                },
                "sales_period": "Q1-2025",
                "goal": "10000.00",
                "accumulate": "0.00",
                "status": "in_progress",
                "created_at": "2025-10-18T00:00:00Z",
                "updated_at": "2025-10-18T00:00:00Z"
            }
        )

        result = await seller_adapter.create_sales_plan(sales_plan_data)

        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert call_args.args[0] == "/seller/sales-plans"

        # Verify adapter extracts id and constructs response correctly
        assert result.id == "test-id"
        assert result.message == "Sales plan created successfully"


class TestSellerAdapterGetSalesPlans:
    """Test get_sales_plans calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, seller_adapter, mock_http_client):
        """Test that GET /sales-plans is called."""
        mock_http_client.get = AsyncMock(
            return_value={
                "items": [],
                "total": 0,
                "page": 1,
                "size": 10,
                "has_next": False,
                "has_previous": False,
            }
        )

        await seller_adapter.get_sales_plans()

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert call_args.args[0] == "/seller/sales-plans"


class TestSellerAdapterGetSellerSalesPlans:
    """Test get_seller_sales_plans calls correct endpoint."""

    @pytest.mark.asyncio
    async def test_calls_correct_endpoint(self, seller_adapter, mock_http_client):
        """Test that GET /sellers/{id}/sales-plans is called."""
        seller_id = UUID("550e8400-e29b-41d4-a716-446655440000")

        mock_http_client.get = AsyncMock(
            return_value={
                "items": [],
                "total": 0,
                "page": 1,
                "size": 10,
                "has_next": False,
                "has_previous": False,
            }
        )

        await seller_adapter.get_seller_sales_plans(seller_id)

        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert call_args.args[0] == f"/seller/sellers/{seller_id}/sales-plans"
