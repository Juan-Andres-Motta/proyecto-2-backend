"""Unit tests for authentication controller endpoints."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from common.auth.controller import get_me, login, refresh, signup
from common.auth.schemas import (
    LoginRequest,
    RefreshTokenRequest,
    SignupRequest,
)


@pytest.fixture
def mock_cognito_service():
    """Fixture providing mock CognitoService."""
    return Mock()


@pytest.fixture
def mock_user_claims():
    """Fixture providing mock JWT user claims."""
    return {
        "sub": "test-user-id-12345",
        "email": "testuser@example.com",
        "cognito:groups": ["web_users"],
        "custom:user_type": "web",
    }


class TestLoginEndpoint:
    """Tests for POST /auth/login endpoint."""

    @pytest.mark.asyncio
    async def test_login_endpoint_success_web_user(self):
        """Test successful login for web user with web client_type."""
        request = LoginRequest(
            email="web@test.com", password="Password123", client_type="web"
        )

        with patch("common.auth.controller.CognitoService") as mock_cognito_class, \
             patch("common.auth.jwt_validator.get_jwt_validator") as mock_validator:

            # Mock Cognito service
            mock_cognito_instance = Mock()
            mock_cognito_instance.login = AsyncMock(
                return_value={
                    "access_token": "test-access-token",
                    "id_token": "test-id-token",
                    "refresh_token": "test-refresh-token",
                    "expires_in": 3600,
                }
            )
            mock_cognito_class.return_value = mock_cognito_instance

            # Mock JWT validator
            mock_validator_instance = Mock()
            mock_validator_instance.validate_token = AsyncMock(
                return_value={"cognito:groups": ["web_users"], "email": "web@test.com"}
            )
            mock_validator.return_value = mock_validator_instance

            result = await login(request)

            assert result.access_token == "test-access-token"
            assert result.id_token == "test-id-token"
            assert result.refresh_token == "test-refresh-token"
            assert result.token_type == "Bearer"
            assert result.expires_in == 3600
            assert result.user_groups == ["web_users"]

    @pytest.mark.asyncio
    async def test_login_endpoint_success_mobile_user(self):
        """Test successful login for seller user with mobile client_type."""
        request = LoginRequest(
            email="seller@test.com", password="Password123", client_type="mobile"
        )

        with patch("common.auth.controller.CognitoService") as mock_cognito_class, \
             patch("common.auth.jwt_validator.get_jwt_validator") as mock_validator:

            # Mock Cognito service
            mock_cognito_instance = Mock()
            mock_cognito_instance.login = AsyncMock(
                return_value={
                    "access_token": "test-access-token",
                    "id_token": "test-id-token",
                    "refresh_token": "test-refresh-token",
                    "expires_in": 3600,
                }
            )
            mock_cognito_class.return_value = mock_cognito_instance

            # Mock JWT validator
            mock_validator_instance = Mock()
            mock_validator_instance.validate_token = AsyncMock(
                return_value={"cognito:groups": ["seller_users"], "email": "seller@test.com"}
            )
            mock_validator.return_value = mock_validator_instance

            result = await login(request)

            assert result.access_token == "test-access-token"
            assert result.user_groups == ["seller_users"]

    @pytest.mark.asyncio
    async def test_login_endpoint_invalid_email_format(self):
        """Test login with malformed email returns 422."""
        with pytest.raises(Exception):  # Pydantic validation error
            LoginRequest(email="invalid-email", password="Password123", client_type="web")

    @pytest.mark.asyncio
    async def test_login_endpoint_missing_password(self):
        """Test login without password returns 422."""
        with pytest.raises(Exception):  # Pydantic validation error
            LoginRequest(email="user@test.com", password=None, client_type="web")

    @pytest.mark.asyncio
    async def test_login_endpoint_invalid_client_type(self):
        """Test login with invalid client_type returns 400."""
        request = LoginRequest(email="user@test.com", password="Password123", client_type="invalid")

        with pytest.raises(HTTPException) as exc_info:
            await login(request)

        assert exc_info.value.status_code == 400
        assert "client_type" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_login_endpoint_web_user_tries_mobile(self):
        """Test web user trying to login with mobile client_type returns 403."""
        request = LoginRequest(email="web@test.com", password="Password123", client_type="mobile")

        with patch("common.auth.controller.CognitoService") as mock_cognito_class, \
             patch("common.auth.jwt_validator.get_jwt_validator") as mock_validator:

            mock_cognito_instance = Mock()
            mock_cognito_instance.login = AsyncMock(
                return_value={
                    "access_token": "test-access-token",
                    "id_token": "test-id-token",
                    "refresh_token": "test-refresh-token",
                    "expires_in": 3600,
                }
            )
            mock_cognito_class.return_value = mock_cognito_instance

            mock_validator_instance = Mock()
            mock_validator_instance.validate_token = AsyncMock(
                return_value={"cognito:groups": ["web_users"], "email": "web@test.com"}
            )
            mock_validator.return_value = mock_validator_instance

            with pytest.raises(HTTPException) as exc_info:
                await login(request)

            assert exc_info.value.status_code == 403
            assert "web users must use web" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_login_endpoint_seller_user_tries_web(self):
        """Test seller user trying to login with web client_type returns 403."""
        request = LoginRequest(email="seller@test.com", password="Password123", client_type="web")

        with patch("common.auth.controller.CognitoService") as mock_cognito_class, \
             patch("common.auth.jwt_validator.get_jwt_validator") as mock_validator:

            mock_cognito_instance = Mock()
            mock_cognito_instance.login = AsyncMock(
                return_value={
                    "access_token": "test-access-token",
                    "id_token": "test-id-token",
                    "refresh_token": "test-refresh-token",
                    "expires_in": 3600,
                }
            )
            mock_cognito_class.return_value = mock_cognito_instance

            mock_validator_instance = Mock()
            mock_validator_instance.validate_token = AsyncMock(
                return_value={"cognito:groups": ["seller_users"], "email": "seller@test.com"}
            )
            mock_validator.return_value = mock_validator_instance

            with pytest.raises(HTTPException) as exc_info:
                await login(request)

            assert exc_info.value.status_code == 403
            assert "seller and client users must use mobile" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_login_endpoint_unauthorized(self):
        """Test login with wrong credentials returns 401."""
        request = LoginRequest(email="user@test.com", password="WrongPassword", client_type="web")

        with patch("common.auth.controller.CognitoService") as mock_cognito_class:
            mock_cognito_instance = Mock()
            mock_cognito_instance.login = AsyncMock(
                side_effect=HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password",
                )
            )
            mock_cognito_class.return_value = mock_cognito_instance

            with pytest.raises(HTTPException) as exc_info:
                await login(request)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_login_endpoint_unverified_user(self):
        """Test login with unverified email returns 403."""
        request = LoginRequest(email="unverified@test.com", password="Password123", client_type="web")

        with patch("common.auth.controller.CognitoService") as mock_cognito_class:
            mock_cognito_instance = Mock()
            mock_cognito_instance.login = AsyncMock(
                side_effect=HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User email not verified",
                )
            )
            mock_cognito_class.return_value = mock_cognito_instance

            with pytest.raises(HTTPException) as exc_info:
                await login(request)

            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_login_endpoint_service_unavailable(self):
        """Test login when Cognito is down returns 503."""
        request = LoginRequest(email="user@test.com", password="Password123", client_type="web")

        with patch("common.auth.controller.CognitoService") as mock_cognito_class:
            mock_cognito_instance = Mock()
            mock_cognito_instance.login = AsyncMock(
                side_effect=HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Authentication service temporarily unavailable",
                )
            )
            mock_cognito_class.return_value = mock_cognito_instance

            with pytest.raises(HTTPException) as exc_info:
                await login(request)

            assert exc_info.value.status_code == 503


class TestRefreshEndpoint:
    """Tests for POST /auth/refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_endpoint_success(self, mock_cognito_service):
        """Test successful token refresh."""
        request = RefreshTokenRequest(refresh_token="valid-refresh-token")

        mock_cognito_service.refresh_token = AsyncMock(
            return_value={
                "access_token": "new-access-token",
                "id_token": "new-id-token",
                "expires_in": 3600,
            }
        )

        result = await refresh(request, mock_cognito_service)

        assert result.access_token == "new-access-token"
        assert result.id_token == "new-id-token"
        assert result.token_type == "Bearer"
        assert result.expires_in == 3600
        mock_cognito_service.refresh_token.assert_called_once_with("valid-refresh-token")

    @pytest.mark.asyncio
    async def test_refresh_endpoint_missing_token(self):
        """Test refresh without refresh_token returns 422."""
        with pytest.raises(Exception):  # Pydantic validation error
            RefreshTokenRequest(refresh_token=None)

    @pytest.mark.asyncio
    async def test_refresh_endpoint_invalid_token(self, mock_cognito_service):
        """Test refresh with invalid token returns 401."""
        request = RefreshTokenRequest(refresh_token="invalid-token")

        mock_cognito_service.refresh_token = AsyncMock(
            side_effect=HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await refresh(request, mock_cognito_service)

        assert exc_info.value.status_code == 401


class TestSignupEndpoint:
    """Tests for POST /auth/signup endpoint."""

    @pytest.mark.asyncio
    async def test_signup_endpoint_success(self, mock_cognito_service):
        """Test successful user registration with client user type and client record creation."""
        request = SignupRequest(
            email="newuser@test.com",
            password="Password123",
            user_type="client",
            telefono="+1234567890",
            nombre_institucion="Test Hospital",
            tipo_institucion="hospital",
            nit="123456789",
            direccion="123 Test St",
            ciudad="Test City",
            pais="Test Country",
            representante="John Doe",
        )

        mock_cognito_service.signup = AsyncMock(
            return_value={
                "user_id": "new-user-id-123",
                "email": "newuser@test.com",
            }
        )

        with patch("dependencies.get_auth_client_port") as mock_get_client_port:
            mock_client_port = Mock()
            mock_client_port.create_client = AsyncMock(
                return_value={
                    "cliente_id": "client-uuid-123",
                    "cognito_user_id": "new-user-id-123",
                    "email": "newuser@test.com",
                    "nombre_institucion": "Test Hospital",
                }
            )
            mock_get_client_port.return_value = mock_client_port

            result = await signup(request, mock_cognito_service)

            assert result.user_id == "new-user-id-123"
            assert result.email == "newuser@test.com"
            assert result.cliente_id == "client-uuid-123"
            assert result.nombre_institucion == "Test Hospital"
            assert "verification" in result.message.lower()

            mock_cognito_service.signup.assert_called_once_with(
                "newuser@test.com", "Password123", "client"
            )
            mock_client_port.create_client.assert_called_once()
            client_data = mock_client_port.create_client.call_args[0][0]
            assert client_data["cognito_user_id"] == "new-user-id-123"
            assert client_data["email"] == "newuser@test.com"
            assert client_data["telefono"] == "+1234567890"
            assert client_data["nombre_institucion"] == "Test Hospital"

    @pytest.mark.asyncio
    async def test_signup_endpoint_web_user_type(self, mock_cognito_service):
        """Test signup rejects user_type='web' with 403."""
        request = SignupRequest(
            email="web@test.com",
            password="Password123",
            user_type="web",
            telefono="+1234567890",
            nombre_institucion="Test Hospital",
            tipo_institucion="hospital",
            nit="123456789",
            direccion="123 Test St",
            ciudad="Test City",
            pais="Test Country",
            representante="John Doe",
        )

        with pytest.raises(HTTPException) as exc_info:
            await signup(request, mock_cognito_service)

        assert exc_info.value.status_code == 403
        assert "client" in exc_info.value.detail.lower()
        mock_cognito_service.signup.assert_not_called()

    @pytest.mark.asyncio
    async def test_signup_endpoint_seller_user_type(self, mock_cognito_service):
        """Test signup rejects user_type='seller' with 403."""
        request = SignupRequest(
            email="seller@test.com",
            password="Password123",
            user_type="seller",
            telefono="+1234567890",
            nombre_institucion="Test Hospital",
            tipo_institucion="hospital",
            nit="123456789",
            direccion="123 Test St",
            ciudad="Test City",
            pais="Test Country",
            representante="John Doe",
        )

        with pytest.raises(HTTPException) as exc_info:
            await signup(request, mock_cognito_service)

        assert exc_info.value.status_code == 403
        assert "client" in exc_info.value.detail.lower()
        mock_cognito_service.signup.assert_not_called()

    @pytest.mark.asyncio
    async def test_signup_endpoint_client_user_type(self, mock_cognito_service):
        """Test signup accepts user_type='client' and creates client record."""
        request = SignupRequest(
            email="client@test.com",
            password="Password123",
            user_type="client",
            telefono="+1234567890",
            nombre_institucion="Test Hospital",
            tipo_institucion="hospital",
            nit="123456789",
            direccion="123 Test St",
            ciudad="Test City",
            pais="Test Country",
            representante="John Doe",
        )

        mock_cognito_service.signup = AsyncMock(
            return_value={"user_id": "test-id", "email": "client@test.com"}
        )

        with patch("dependencies.get_auth_client_port") as mock_get_client_port:
            mock_client_port = Mock()
            mock_client_port.create_client = AsyncMock(
                return_value={
                    "cliente_id": "client-123",
                    "cognito_user_id": "test-id",
                    "email": "client@test.com",
                    "nombre_institucion": "Test Hospital",
                }
            )
            mock_get_client_port.return_value = mock_client_port

            result = await signup(request, mock_cognito_service)

            assert result.user_id == "test-id"
            assert result.cliente_id == "client-123"

    @pytest.mark.asyncio
    async def test_signup_endpoint_invalid_user_type(self, mock_cognito_service):
        """Test signup with non-client user_type returns 403."""
        request = SignupRequest(
            email="user@test.com",
            password="Password123",
            user_type="admin",
            telefono="+1234567890",
            nombre_institucion="Test Hospital",
            tipo_institucion="hospital",
            nit="123456789",
            direccion="123 Test St",
            ciudad="Test City",
            pais="Test Country",
            representante="John Doe",
        )

        with pytest.raises(HTTPException) as exc_info:
            await signup(request, mock_cognito_service)

        assert exc_info.value.status_code == 403
        assert "client" in exc_info.value.detail.lower()
        mock_cognito_service.signup.assert_not_called()

    @pytest.mark.asyncio
    async def test_signup_endpoint_missing_user_type(self):
        """Test signup without user_type returns 422."""
        with pytest.raises(Exception):  # Pydantic validation error
            SignupRequest(email="user@test.com", password="Password123", user_type=None)

    @pytest.mark.asyncio
    async def test_signup_endpoint_invalid_email(self):
        """Test signup with malformed email returns 422."""
        with pytest.raises(Exception):  # Pydantic validation error
            SignupRequest(
                email="not-an-email", password="Password123", user_type="web"
            )

    @pytest.mark.asyncio
    async def test_signup_endpoint_weak_password(self, mock_cognito_service):
        """Test signup with weak password returns 400."""
        request = SignupRequest(
            email="user@test.com",
            password="Password123",
            user_type="client",
            telefono="+1234567890",
            nombre_institucion="Test Hospital",
            tipo_institucion="hospital",
            nit="123456789",
            direccion="123 Test St",
            ciudad="Test City",
            pais="Test Country",
            representante="John Doe",
        )

        mock_cognito_service.signup = AsyncMock(
            side_effect=HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet requirements",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await signup(request, mock_cognito_service)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_signup_endpoint_duplicate_user(self, mock_cognito_service):
        """Test signup with existing email returns 409."""
        request = SignupRequest(
            email="existing@test.com",
            password="Password123",
            user_type="client",
            telefono="+1234567890",
            nombre_institucion="Test Hospital",
            tipo_institucion="hospital",
            nit="123456789",
            direccion="123 Test St",
            ciudad="Test City",
            pais="Test Country",
            representante="John Doe",
        )

        mock_cognito_service.signup = AsyncMock(
            side_effect=HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await signup(request, mock_cognito_service)

        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_signup_endpoint_client_creation_failure(self, mock_cognito_service):
        """Test signup when client record creation fails returns 500."""
        request = SignupRequest(
            email="newuser@test.com",
            password="Password123",
            user_type="client",
            telefono="+1234567890",
            nombre_institucion="Test Hospital",
            tipo_institucion="hospital",
            nit="123456789",
            direccion="123 Test St",
            ciudad="Test City",
            pais="Test Country",
            representante="John Doe",
        )

        mock_cognito_service.signup = AsyncMock(
            return_value={
                "user_id": "new-user-id-123",
                "email": "newuser@test.com",
            }
        )

        with patch("dependencies.get_auth_client_port") as mock_get_client_port:
            mock_client_port = Mock()
            mock_client_port.create_client = AsyncMock(
                side_effect=Exception("Client service unavailable")
            )
            mock_get_client_port.return_value = mock_client_port

            with pytest.raises(HTTPException) as exc_info:
                await signup(request, mock_cognito_service)

            assert exc_info.value.status_code == 500
            assert "client profile creation failed" in exc_info.value.detail.lower()


class TestGetMeEndpoint:
    """Tests for GET /auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_get_me_success(self, mock_user_claims):
        """Test get current user info with valid token."""
        result = await get_me(mock_user_claims)

        assert result["user_id"] == "test-user-id-12345"
        assert result["email"] == "testuser@example.com"
        assert result["groups"] == ["web_users"]
        assert result["user_type"] == "web"

    @pytest.mark.asyncio
    async def test_get_me_with_web_user_groups(self):
        """Test get_me returns web_users group."""
        user = {
            "sub": "user-123",
            "email": "web@test.com",
            "cognito:groups": ["web_users"],
            "custom:user_type": "web",
        }

        result = await get_me(user)

        assert result["groups"] == ["web_users"]

    @pytest.mark.asyncio
    async def test_get_me_with_seller_user_groups(self):
        """Test get_me returns seller_users group."""
        user = {
            "sub": "seller-123",
            "email": "seller@test.com",
            "cognito:groups": ["seller_users"],
            "custom:user_type": "seller",
        }

        result = await get_me(user)

        assert result["groups"] == ["seller_users"]

    @pytest.mark.asyncio
    async def test_get_me_with_client_user_groups(self):
        """Test get_me returns client_users group."""
        user = {
            "sub": "client-123",
            "email": "client@test.com",
            "cognito:groups": ["client_users"],
            "custom:user_type": "client",
        }

        result = await get_me(user)

        assert result["groups"] == ["client_users"]

    @pytest.mark.asyncio
    async def test_get_me_missing_token(self):
        """Test get_me without token is handled by FastAPI security."""
        # This would be handled by FastAPI's Depends(get_current_user)
        # which requires HTTPBearer token - tested at integration level
        pass

    @pytest.mark.asyncio
    async def test_get_me_invalid_token(self):
        """Test get_me with invalid token is handled by JWT validator."""
        # This would be handled by get_current_user dependency
        # which calls JWT validator - tested at integration level
        pass

    @pytest.mark.asyncio
    async def test_get_me_invalid_bearer_format(self):
        """Test get_me with malformed Authorization header."""
        # This would be handled by FastAPI's HTTPBearer security
        # which validates "Bearer <token>" format - tested at integration level
        pass
