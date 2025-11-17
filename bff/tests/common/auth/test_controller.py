"""
Unit tests for authentication controller.

Tests that controller endpoints properly delegate to AuthService
and handle HTTP request/response correctly.
"""

from unittest.mock import AsyncMock, Mock, patch
import pytest
from fastapi import HTTPException, status

from common.auth.controller import (
    login,
    refresh,
    signup,
    get_me,
    get_auth_service,
)
from common.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    SignupRequest,
    SignupResponse,
    UserMeResponse,
)
from common.auth.auth_service import AuthService
from common.auth.ports import ClientPort


@pytest.fixture
def mock_auth_service():
    """Create a mock AuthService."""
    return Mock(spec=AuthService)


@pytest.fixture
def mock_client_port():
    """Create a mock ClientPort."""
    return Mock(spec=ClientPort)


@pytest.fixture
def sample_login_request():
    """Sample login request."""
    return LoginRequest(
        email="test@example.com",
        password="SecurePass123!"
    )


@pytest.fixture
def sample_refresh_request():
    """Sample refresh token request."""
    return RefreshTokenRequest(
        refresh_token="valid_refresh_token"
    )


@pytest.fixture
def sample_signup_request():
    """Sample signup request."""
    return SignupRequest(
        email="newclient@hospital.com",
        password="SecurePass123!",
        name="John Doe",
        telefono="+1234567890",
        nombre_institucion="Hospital Test",
        tipo_institucion="hospital",
        nit="123456789",
        direccion="123 Test St",
        ciudad="Test City",
        pais="Test Country",
        representante="John Doe",
        user_type="client"
    )


class TestLoginEndpoint:
    """Test /auth/login endpoint."""

    @pytest.mark.asyncio
    async def test_login_calls_service_and_returns_response(
        self,
        mock_auth_service,
        sample_login_request
    ):
        """Test that login calls AuthService and returns LoginResponse."""
        # Arrange
        expected_result = {
            "access_token": "mock_access_token",
            "id_token": "mock_id_token",
            "refresh_token": "mock_refresh_token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "user_groups": [],
        }
        mock_auth_service.login = AsyncMock(return_value=expected_result)

        # Act
        result = await login(sample_login_request, mock_auth_service)

        # Assert
        mock_auth_service.login.assert_called_once_with(sample_login_request)
        assert isinstance(result, LoginResponse)
        assert result.access_token == "mock_access_token"
        assert result.id_token == "mock_id_token"
        assert result.refresh_token == "mock_refresh_token"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials_raises_401(
        self,
        mock_auth_service,
        sample_login_request
    ):
        """Test login with invalid credentials propagates 401."""
        # Arrange
        mock_auth_service.login = AsyncMock(
            side_effect=HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await login(sample_login_request, mock_auth_service)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestRefreshEndpoint:
    """Test /auth/refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_calls_service_and_returns_response(
        self,
        mock_auth_service,
        sample_refresh_request
    ):
        """Test that refresh calls AuthService and returns RefreshTokenResponse."""
        # Arrange
        expected_result = {
            "access_token": "new_access_token",
            "id_token": "new_id_token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        mock_auth_service.refresh_token = AsyncMock(return_value=expected_result)

        # Act
        result = await refresh(sample_refresh_request, mock_auth_service)

        # Assert
        mock_auth_service.refresh_token.assert_called_once_with(
            sample_refresh_request.refresh_token
        )
        assert isinstance(result, RefreshTokenResponse)
        assert result.access_token == "new_access_token"


class TestSignupEndpoint:
    """Test /auth/signup endpoint."""

    @pytest.mark.asyncio
    async def test_signup_calls_service_and_returns_response(
        self,
        mock_auth_service,
        mock_client_port,
        sample_signup_request
    ):
        """Test that signup calls AuthService with correct params."""
        # Arrange
        expected_result = {
            "user_id": "abc123-cognito-user-id",
            "email": "newclient@hospital.com",
        }
        mock_auth_service.signup_client = AsyncMock(return_value=expected_result)

        # Act
        result = await signup(sample_signup_request, mock_auth_service, mock_client_port)

        # Assert
        mock_auth_service.signup_client.assert_called_once_with(
            sample_signup_request,
            mock_client_port
        )
        assert isinstance(result, SignupResponse)
        assert result.user_id == "abc123-cognito-user-id"
        assert result.email == "newclient@hospital.com"

    @pytest.mark.asyncio
    async def test_signup_user_exists_raises_409(
        self,
        mock_auth_service,
        mock_client_port,
        sample_signup_request
    ):
        """Test signup with existing user propagates 409."""
        # Arrange
        mock_auth_service.signup_client = AsyncMock(
            side_effect=HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await signup(sample_signup_request, mock_auth_service, mock_client_port)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT

    @pytest.mark.asyncio
    async def test_signup_saga_rollback_raises_404(
        self,
        mock_auth_service,
        mock_client_port,
        sample_signup_request
    ):
        """Test signup saga rollback propagates 404."""
        # Arrange
        mock_auth_service.signup_client = AsyncMock(
            side_effect=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Failed to complete user registration. Please try again."
            )
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await signup(sample_signup_request, mock_auth_service, mock_client_port)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestGetMeEndpoint:
    """Test /auth/me endpoint with enhanced user details."""

    @pytest.mark.asyncio
    async def test_get_me_returns_seller_user_with_details(self):
        """Test get_me fetches and returns seller details for seller users."""
        # Arrange
        mock_user = {
            "sub": "abc123-seller-id",
            "name": "John Seller",
            "email": "john.seller@example.com",
            "cognito:groups": ["seller_users"],
            "custom:user_type": "seller",
        }

        mock_seller_data = {
            "id": "seller-uuid-123",
            "cognito_user_id": "abc123-seller-id",
            "name": "John Seller",
            "email": "john.seller@example.com",
            "phone": "+1234567890",
            "city": "New York",
            "country": "USA",
        }

        mock_seller_adapter = Mock()
        mock_seller_adapter.get_seller_by_cognito_user_id = AsyncMock(
            return_value=mock_seller_data
        )

        # Act
        with patch("dependencies.get_seller_app_seller_port", return_value=mock_seller_adapter):
            result = await get_me(mock_user)

        # Assert
        assert isinstance(result, UserMeResponse)
        assert result.user_id == "abc123-seller-id"
        assert result.name == "John Seller"
        assert result.email == "john.seller@example.com"
        assert result.groups == ["seller_users"]
        assert result.user_type == "seller"
        assert result.user_details == mock_seller_data
        mock_seller_adapter.get_seller_by_cognito_user_id.assert_called_once_with("abc123-seller-id")

    @pytest.mark.asyncio
    async def test_get_me_returns_client_user_with_details(self):
        """Test get_me fetches and returns client details for client users."""
        # Arrange
        mock_user = {
            "sub": "abc123-client-id",
            "name": "Jane Client",
            "email": "jane.client@hospital.com",
            "cognito:groups": ["client_users"],
            "custom:user_type": "client",
        }

        mock_client_data = {
            "cliente_id": "client-uuid-456",
            "cognito_user_id": "abc123-client-id",
            "email": "jane.client@hospital.com",
            "telefono": "+1234567890",
            "nombre_institucion": "Test Hospital",
            "tipo_institucion": "hospital",
            "nit": "123456789",
            "direccion": "123 Test St",
            "ciudad": "Boston",
            "pais": "USA",
            "representante": "Jane Client",
        }

        mock_client_adapter = Mock()
        mock_client_adapter.get_client_by_cognito_user_id = AsyncMock(
            return_value=mock_client_data
        )

        # Act
        with patch("dependencies.get_client_app_client_port", return_value=mock_client_adapter):
            result = await get_me(mock_user)

        # Assert
        assert isinstance(result, UserMeResponse)
        assert result.user_id == "abc123-client-id"
        assert result.name == "Jane Client"
        assert result.email == "jane.client@hospital.com"
        assert result.groups == ["client_users"]
        assert result.user_type == "client"
        assert result.user_details == mock_client_data
        mock_client_adapter.get_client_by_cognito_user_id.assert_called_once_with("abc123-client-id")

    @pytest.mark.asyncio
    async def test_get_me_returns_web_user_without_details(self):
        """Test get_me returns only JWT claims for web users (no additional details)."""
        # Arrange
        mock_user = {
            "sub": "abc123-web-user-id",
            "name": "Web Admin",
            "email": "admin@example.com",
            "cognito:groups": ["web_users"],
            "custom:user_type": "web",
        }

        # Act
        result = await get_me(mock_user)

        # Assert
        assert isinstance(result, UserMeResponse)
        assert result.user_id == "abc123-web-user-id"
        assert result.name == "Web Admin"
        assert result.email == "admin@example.com"
        assert result.groups == ["web_users"]
        assert result.user_type == "web"
        assert result.user_details is None

    @pytest.mark.asyncio
    async def test_get_me_handles_missing_groups(self):
        """Test get_me returns empty list when groups are missing."""
        # Arrange
        mock_user = {
            "sub": "abc123-user-id",
            "name": "John Doe",
            "email": "john@example.com",
            "custom:user_type": "web",
        }

        # Act
        result = await get_me(mock_user)

        # Assert
        assert isinstance(result, UserMeResponse)
        assert result.groups == []

    @pytest.mark.asyncio
    async def test_get_me_handles_seller_fetch_failure_gracefully(self):
        """Test get_me handles seller adapter errors gracefully."""
        # Arrange
        mock_user = {
            "sub": "abc123-seller-id",
            "name": "John Seller",
            "email": "john.seller@example.com",
            "cognito:groups": ["seller_users"],
            "custom:user_type": "seller",
        }

        mock_seller_adapter = Mock()
        mock_seller_adapter.get_seller_by_cognito_user_id = AsyncMock(
            side_effect=Exception("Service unavailable")
        )

        # Act
        with patch("dependencies.get_seller_app_seller_port", return_value=mock_seller_adapter):
            result = await get_me(mock_user)

        # Assert - Should return JWT claims even if adapter fails
        assert isinstance(result, UserMeResponse)
        assert result.user_id == "abc123-seller-id"
        assert result.name == "John Seller"
        assert result.email == "john.seller@example.com"
        assert result.user_type == "seller"
        assert result.user_details is None  # Should be None when fetch fails

    @pytest.mark.asyncio
    async def test_get_me_handles_client_fetch_failure_gracefully(self):
        """Test get_me handles client adapter errors gracefully."""
        # Arrange
        mock_user = {
            "sub": "abc123-client-id",
            "name": "Jane Client",
            "email": "jane.client@hospital.com",
            "cognito:groups": ["client_users"],
            "custom:user_type": "client",
        }

        mock_client_adapter = Mock()
        mock_client_adapter.get_client_by_cognito_user_id = AsyncMock(
            side_effect=Exception("Service unavailable")
        )

        # Act
        with patch("dependencies.get_client_app_client_port", return_value=mock_client_adapter):
            result = await get_me(mock_user)

        # Assert - Should return JWT claims even if adapter fails
        assert isinstance(result, UserMeResponse)
        assert result.user_id == "abc123-client-id"
        assert result.name == "Jane Client"
        assert result.email == "jane.client@hospital.com"
        assert result.user_type == "client"
        assert result.user_details is None  # Should be None when fetch fails


class TestDependencies:
    """Test dependency injection functions."""

    def test_get_auth_service_returns_auth_service(self):
        """Test get_auth_service returns AuthService instance."""
        # Arrange
        from common.auth.cognito_service import CognitoService
        mock_cognito = Mock(spec=CognitoService)

        # Act
        result = get_auth_service(mock_cognito)

        # Assert
        assert isinstance(result, AuthService)
        assert result.cognito_service == mock_cognito
