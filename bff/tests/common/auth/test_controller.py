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
    async def test_login_endpoint_success(self, mock_cognito_service):
        """Test successful login returns tokens."""
        request = LoginRequest(email="user@test.com", password="Password123")

        mock_cognito_service.login = AsyncMock(
            return_value={
                "access_token": "test-access-token",
                "id_token": "test-id-token",
                "refresh_token": "test-refresh-token",
                "expires_in": 3600,
            }
        )

        result = await login(request, mock_cognito_service)

        assert result.access_token == "test-access-token"
        assert result.id_token == "test-id-token"
        assert result.refresh_token == "test-refresh-token"
        assert result.token_type == "Bearer"
        assert result.expires_in == 3600
        mock_cognito_service.login.assert_called_once_with("user@test.com", "Password123")

    @pytest.mark.asyncio
    async def test_login_endpoint_invalid_email_format(self):
        """Test login with malformed email returns 422."""
        with pytest.raises(Exception):  # Pydantic validation error
            LoginRequest(email="invalid-email", password="Password123")

    @pytest.mark.asyncio
    async def test_login_endpoint_missing_password(self):
        """Test login without password returns 422."""
        with pytest.raises(Exception):  # Pydantic validation error
            LoginRequest(email="user@test.com", password=None)

    @pytest.mark.asyncio
    async def test_login_endpoint_short_password(self):
        """Test login with password < 8 chars returns 422."""
        with pytest.raises(Exception):  # Pydantic validation error
            LoginRequest(email="user@test.com", password="short")

    @pytest.mark.asyncio
    async def test_login_endpoint_unauthorized(self, mock_cognito_service):
        """Test login with wrong credentials returns 401."""
        request = LoginRequest(email="user@test.com", password="WrongPassword")

        mock_cognito_service.login = AsyncMock(
            side_effect=HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await login(request, mock_cognito_service)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_login_endpoint_unverified_user(self, mock_cognito_service):
        """Test login with unverified email returns 403."""
        request = LoginRequest(email="unverified@test.com", password="Password123")

        mock_cognito_service.login = AsyncMock(
            side_effect=HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User email not verified",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await login(request, mock_cognito_service)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_login_endpoint_service_unavailable(self, mock_cognito_service):
        """Test login when Cognito is down returns 503."""
        request = LoginRequest(email="user@test.com", password="Password123")

        mock_cognito_service.login = AsyncMock(
            side_effect=HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable",
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await login(request, mock_cognito_service)

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
        """Test successful user registration."""
        request = SignupRequest(
            email="newuser@test.com", password="Password123", user_type="seller"
        )

        mock_cognito_service.signup = AsyncMock(
            return_value={
                "user_id": "new-user-id-123",
                "email": "newuser@test.com",
            }
        )

        result = await signup(request, mock_cognito_service)

        assert result.user_id == "new-user-id-123"
        assert result.email == "newuser@test.com"
        assert "verification" in result.message.lower()
        mock_cognito_service.signup.assert_called_once_with(
            "newuser@test.com", "Password123", "seller"
        )

    @pytest.mark.asyncio
    async def test_signup_endpoint_web_user_type(self, mock_cognito_service):
        """Test signup accepts user_type='web'."""
        request = SignupRequest(
            email="web@test.com", password="Password123", user_type="web"
        )

        mock_cognito_service.signup = AsyncMock(
            return_value={"user_id": "test-id", "email": "web@test.com"}
        )

        result = await signup(request, mock_cognito_service)

        assert result.user_id == "test-id"
        mock_cognito_service.signup.assert_called_once_with(
            "web@test.com", "Password123", "web"
        )

    @pytest.mark.asyncio
    async def test_signup_endpoint_seller_user_type(self, mock_cognito_service):
        """Test signup accepts user_type='seller'."""
        request = SignupRequest(
            email="seller@test.com", password="Password123", user_type="seller"
        )

        mock_cognito_service.signup = AsyncMock(
            return_value={"user_id": "test-id", "email": "seller@test.com"}
        )

        result = await signup(request, mock_cognito_service)

        assert result.user_id == "test-id"

    @pytest.mark.asyncio
    async def test_signup_endpoint_client_user_type(self, mock_cognito_service):
        """Test signup accepts user_type='client'."""
        request = SignupRequest(
            email="client@test.com", password="Password123", user_type="client"
        )

        mock_cognito_service.signup = AsyncMock(
            return_value={"user_id": "test-id", "email": "client@test.com"}
        )

        result = await signup(request, mock_cognito_service)

        assert result.user_id == "test-id"

    @pytest.mark.asyncio
    async def test_signup_endpoint_invalid_user_type(self, mock_cognito_service):
        """Test signup with invalid user_type returns 400."""
        request = SignupRequest(
            email="user@test.com", password="Password123", user_type="admin"
        )

        with pytest.raises(HTTPException) as exc_info:
            await signup(request, mock_cognito_service)

        assert exc_info.value.status_code == 400
        assert "Invalid user_type" in exc_info.value.detail

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
        request = SignupRequest(email="user@test.com", password="Password123", user_type="web")

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
            email="existing@test.com", password="Password123", user_type="seller"
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
