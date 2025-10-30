"""
Unit tests for authentication controller.

Tests that controller endpoints properly delegate to AuthService
and handle HTTP request/response correctly.
"""

from unittest.mock import AsyncMock, Mock
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
    """Test /auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_get_me_returns_user_claims(self):
        """Test get_me extracts and returns user information from JWT."""
        # Arrange
        mock_user = {
            "sub": "abc123-user-id",
            "name": "John Doe",
            "email": "john@example.com",
            "cognito:groups": ["client"],
            "custom:user_type": "client",
        }

        # Act
        result = await get_me(mock_user)

        # Assert
        assert result["user_id"] == "abc123-user-id"
        assert result["name"] == "John Doe"
        assert result["email"] == "john@example.com"
        assert result["groups"] == ["client"]
        assert result["user_type"] == "client"

    @pytest.mark.asyncio
    async def test_get_me_handles_missing_groups(self):
        """Test get_me returns empty list when groups are missing."""
        # Arrange
        mock_user = {
            "sub": "abc123-user-id",
            "name": "John Doe",
            "email": "john@example.com",
            "custom:user_type": "client",
        }

        # Act
        result = await get_me(mock_user)

        # Assert
        assert result["groups"] == []


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
