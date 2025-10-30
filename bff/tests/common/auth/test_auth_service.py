"""
Unit tests for AuthService.

Tests the business logic layer for authentication operations
including login, token refresh, and client signup with saga pattern.
"""

from unittest.mock import AsyncMock, Mock, patch
import pytest
from fastapi import HTTPException, status

from common.auth.auth_service import AuthService
from common.auth.cognito_service import CognitoService
from common.auth.ports import ClientPort
from common.auth.schemas import LoginRequest, SignupRequest


@pytest.fixture
def mock_cognito_service():
    """Create a mock Cognito service."""
    return Mock(spec=CognitoService)


@pytest.fixture
def mock_client_port():
    """Create a mock client port."""
    return Mock(spec=ClientPort)


@pytest.fixture
def auth_service(mock_cognito_service):
    """Create AuthService instance with mocked dependencies."""
    return AuthService(cognito_service=mock_cognito_service)


@pytest.fixture
def sample_login_request():
    """Sample login request."""
    return LoginRequest(
        email="test@example.com",
        password="SecurePass123!"
    )


@pytest.fixture
def sample_signup_request():
    """Sample signup request with all client fields."""
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


@pytest.fixture
def sample_cognito_tokens():
    """Sample Cognito authentication tokens."""
    return {
        "access_token": "mock_access_token",
        "id_token": "mock_id_token",
        "refresh_token": "mock_refresh_token",
        "expires_in": 3600,
    }


@pytest.fixture
def sample_cognito_user():
    """Sample Cognito user creation response."""
    return {
        "user_id": "abc123-cognito-user-id",
        "username": "newclient",
        "email": "newclient@hospital.com",
    }


class TestAuthServiceLogin:
    """Test login method."""

    @pytest.mark.asyncio
    async def test_login_success(
        self,
        auth_service,
        mock_cognito_service,
        sample_login_request,
        sample_cognito_tokens
    ):
        """Test successful login returns tokens."""
        # Arrange
        mock_cognito_service.login = AsyncMock(return_value=sample_cognito_tokens)

        # Act
        result = await auth_service.login(sample_login_request)

        # Assert
        mock_cognito_service.login.assert_called_once_with(
            sample_login_request.email,
            sample_login_request.password
        )
        assert result["access_token"] == "mock_access_token"
        assert result["id_token"] == "mock_id_token"
        assert result["refresh_token"] == "mock_refresh_token"
        assert result["token_type"] == "Bearer"
        assert result["expires_in"] == 3600
        assert result["user_groups"] == []

    @pytest.mark.asyncio
    async def test_login_cognito_error_propagates(
        self,
        auth_service,
        mock_cognito_service,
        sample_login_request
    ):
        """Test that Cognito errors propagate to caller."""
        # Arrange
        mock_cognito_service.login = AsyncMock(
            side_effect=HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.login(sample_login_request)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Incorrect email or password"


class TestAuthServiceRefreshToken:
    """Test refresh_token method."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self,
        auth_service,
        mock_cognito_service
    ):
        """Test successful token refresh."""
        # Arrange
        refresh_token = "valid_refresh_token"
        expected_tokens = {
            "access_token": "new_access_token",
            "id_token": "new_id_token",
            "expires_in": 3600,
        }
        mock_cognito_service.refresh_token = AsyncMock(return_value=expected_tokens)

        # Act
        result = await auth_service.refresh_token(refresh_token)

        # Assert
        mock_cognito_service.refresh_token.assert_called_once_with(refresh_token)
        assert result["access_token"] == "new_access_token"
        assert result["id_token"] == "new_id_token"
        assert result["token_type"] == "Bearer"
        assert result["expires_in"] == 3600

    @pytest.mark.asyncio
    async def test_refresh_token_invalid_token(
        self,
        auth_service,
        mock_cognito_service
    ):
        """Test refresh with invalid token raises error."""
        # Arrange
        mock_cognito_service.refresh_token = AsyncMock(
            side_effect=HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.refresh_token("invalid_token")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthServiceSignupClient:
    """Test signup_client method with saga pattern."""

    @pytest.mark.asyncio
    async def test_signup_success_saga_completes(
        self,
        auth_service,
        mock_cognito_service,
        mock_client_port,
        sample_signup_request,
        sample_cognito_user
    ):
        """Test successful signup completes full saga."""
        # Arrange
        mock_cognito_service.create_user = AsyncMock(return_value=sample_cognito_user)
        mock_client_port.create_client = AsyncMock(return_value={"cliente_id": "client-123"})

        # Act
        result = await auth_service.signup_client(sample_signup_request, mock_client_port)

        # Assert - Step 1: Cognito user created
        mock_cognito_service.create_user.assert_called_once_with(
            email=sample_signup_request.email,
            password=sample_signup_request.password,
            name=sample_signup_request.name,
            user_type=sample_signup_request.user_type,
        )

        # Assert - Step 2: Client record created
        mock_client_port.create_client.assert_called_once()
        client_data_arg = mock_client_port.create_client.call_args[0][0]
        assert client_data_arg["cognito_user_id"] == sample_cognito_user["user_id"]
        assert client_data_arg["email"] == sample_signup_request.email
        assert client_data_arg["telefono"] == sample_signup_request.telefono
        assert client_data_arg["nombre_institucion"] == sample_signup_request.nombre_institucion

        # Assert - Return value
        assert result["user_id"] == sample_cognito_user["user_id"]
        assert result["email"] == sample_signup_request.email

    @pytest.mark.asyncio
    async def test_signup_step2_fails_rollback_success(
        self,
        auth_service,
        mock_cognito_service,
        mock_client_port,
        sample_signup_request,
        sample_cognito_user
    ):
        """Test saga rollback when client creation fails."""
        # Arrange
        mock_cognito_service.create_user = AsyncMock(return_value=sample_cognito_user)
        mock_client_port.create_client = AsyncMock(
            side_effect=Exception("Client microservice unavailable")
        )
        mock_cognito_service.delete_user = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.signup_client(sample_signup_request, mock_client_port)

        # Assert - 404 error returned as requested
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Failed to complete user registration" in exc_info.value.detail

        # Assert - Cognito user was created
        mock_cognito_service.create_user.assert_called_once()

        # Assert - Client creation was attempted
        mock_client_port.create_client.assert_called_once()

        # Assert - Rollback: Cognito user was deleted
        mock_cognito_service.delete_user.assert_called_once_with(sample_cognito_user["username"])

    @pytest.mark.asyncio
    async def test_signup_step2_fails_rollback_fails(
        self,
        auth_service,
        mock_cognito_service,
        mock_client_port,
        sample_signup_request,
        sample_cognito_user
    ):
        """Test saga when rollback also fails - requires manual intervention."""
        # Arrange
        mock_cognito_service.create_user = AsyncMock(return_value=sample_cognito_user)
        mock_client_port.create_client = AsyncMock(
            side_effect=Exception("Client creation failed")
        )
        mock_cognito_service.delete_user = AsyncMock(
            side_effect=Exception("Rollback failed")
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.signup_client(sample_signup_request, mock_client_port)

        # Assert - Still returns 404
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

        # Assert - Rollback was attempted
        mock_cognito_service.delete_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_signup_step1_fails_no_rollback_needed(
        self,
        auth_service,
        mock_cognito_service,
        mock_client_port,
        sample_signup_request
    ):
        """Test that if Step 1 (Cognito) fails, no rollback is needed."""
        # Arrange
        mock_cognito_service.create_user = AsyncMock(
            side_effect=HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.signup_client(sample_signup_request, mock_client_port)

        # Assert - Original error propagates
        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "User already exists" in exc_info.value.detail

        # Assert - Client creation never attempted
        mock_client_port.create_client.assert_not_called()

        # Assert - No rollback needed
        mock_cognito_service.delete_user = AsyncMock()
        mock_cognito_service.delete_user.assert_not_called()


class TestAuthServiceRollbackCognitoUser:
    """Test _rollback_cognito_user helper method."""

    @pytest.mark.asyncio
    async def test_rollback_success(
        self,
        auth_service,
        mock_cognito_service
    ):
        """Test successful rollback returns True."""
        # Arrange
        mock_cognito_service.delete_user = AsyncMock(return_value=None)
        username = "testuser"

        # Act
        result = await auth_service._rollback_cognito_user(username)

        # Assert
        assert result is True
        mock_cognito_service.delete_user.assert_called_once_with(username)

    @pytest.mark.asyncio
    async def test_rollback_failure(
        self,
        auth_service,
        mock_cognito_service
    ):
        """Test failed rollback returns False."""
        # Arrange
        mock_cognito_service.delete_user = AsyncMock(
            side_effect=Exception("Delete failed")
        )
        username = "testuser"

        # Act
        result = await auth_service._rollback_cognito_user(username)

        # Assert
        assert result is False
        mock_cognito_service.delete_user.assert_called_once_with(username)
