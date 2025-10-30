"""Unit tests for CognitoService."""

import base64
import hashlib
import hmac
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from fastapi import HTTPException

from common.auth.cognito_service import CognitoService


@pytest.fixture
def cognito_service():
    """Fixture providing CognitoService instance without client secret."""
    return CognitoService(
        user_pool_id="us-east-1_TestPool",
        client_id="test-client-id",
        client_secret=None,
        region="us-east-1",
    )


@pytest.fixture
def cognito_service_with_secret():
    """Fixture providing CognitoService instance with client secret."""
    return CognitoService(
        user_pool_id="us-east-1_TestPool",
        client_id="test-client-id",
        client_secret="test-client-secret",
        region="us-east-1",
    )


class TestCognitoServiceLogin:
    """Tests for CognitoService.login() method."""

    @pytest.mark.asyncio
    async def test_login_success(self, cognito_service):
        """Test successful login with valid credentials."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "AuthenticationResult": {
                "AccessToken": "test-access-token",
                "IdToken": "test-id-token",
                "RefreshToken": "test-refresh-token",
                "ExpiresIn": 3600,
            }
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await cognito_service.login("user@test.com", "Password123")

            assert result["access_token"] == "test-access-token"
            assert result["id_token"] == "test-id-token"
            assert result["refresh_token"] == "test-refresh-token"
            assert result["expires_in"] == 3600

    @pytest.mark.asyncio
    async def test_login_with_secret_hash(self, cognito_service_with_secret):
        """Test login includes SECRET_HASH when client_secret is provided."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "AuthenticationResult": {
                "AccessToken": "test-access-token",
                "IdToken": "test-id-token",
                "RefreshToken": "test-refresh-token",
                "ExpiresIn": 3600,
            }
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            await cognito_service_with_secret.login("user@test.com", "Password123")

            # Verify SECRET_HASH was included in the request
            call_args = mock_post.call_args
            body = call_args.kwargs["json"]
            assert "SECRET_HASH" in body["AuthParameters"]

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, cognito_service):
        """Test login with incorrect password returns 401."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "__type": "NotAuthorizedException",
            "message": "Incorrect username or password.",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(HTTPException) as exc_info:
                await cognito_service.login("user@test.com", "WrongPassword")

            assert exc_info.value.status_code == 401
            assert "Incorrect email or password" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, cognito_service):
        """Test login with non-existent user returns 401."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "__type": "UserNotFoundException",
            "message": "User does not exist.",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(HTTPException) as exc_info:
                await cognito_service.login("nonexistent@test.com", "Password123")

            assert exc_info.value.status_code == 401
            assert "User not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_login_user_not_confirmed(self, cognito_service):
        """Test login with unverified email returns 403."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "__type": "UserNotConfirmedException",
            "message": "User is not confirmed.",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(HTTPException) as exc_info:
                await cognito_service.login("unverified@test.com", "Password123")

            assert exc_info.value.status_code == 403
            assert "User email not verified" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_login_cognito_service_unavailable(self, cognito_service):
        """Test login when Cognito service is down returns 503."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.ConnectError("Connection failed")
            )

            with pytest.raises(HTTPException) as exc_info:
                await cognito_service.login("user@test.com", "Password123")

            assert exc_info.value.status_code == 503
            assert "temporarily unavailable" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_login_unknown_cognito_error(self, cognito_service):
        """Test login handles unexpected Cognito errors."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {
            "__type": "InternalServerError",
            "message": "Internal server error",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(HTTPException) as exc_info:
                await cognito_service.login("user@test.com", "Password123")

            assert exc_info.value.status_code == 500
            assert "Authentication error" in exc_info.value.detail


class TestCognitoServiceRefreshToken:
    """Tests for CognitoService.refresh_token() method."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, cognito_service):
        """Test successful token refresh."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "AuthenticationResult": {
                "AccessToken": "new-access-token",
                "IdToken": "new-id-token",
                "ExpiresIn": 3600,
            }
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await cognito_service.refresh_token("valid-refresh-token")

            assert result["access_token"] == "new-access-token"
            assert result["id_token"] == "new-id-token"
            assert result["expires_in"] == 3600

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, cognito_service):
        """Test refresh with invalid token returns 401."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "__type": "NotAuthorizedException",
            "message": "Invalid Refresh Token",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(HTTPException) as exc_info:
                await cognito_service.refresh_token("invalid-token")

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token_expired(self, cognito_service):
        """Test refresh with expired token returns 401."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "__type": "NotAuthorizedException",
            "message": "Refresh Token has expired",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(HTTPException) as exc_info:
                await cognito_service.refresh_token("expired-token")

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token_service_unavailable(self, cognito_service):
        """Test refresh when Cognito service is down returns 503."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.ReadTimeout("Request timeout")
            )

            with pytest.raises(HTTPException) as exc_info:
                await cognito_service.refresh_token("valid-token")

            assert exc_info.value.status_code == 503
            assert "temporarily unavailable" in exc_info.value.detail


class TestCognitoServiceCreateUser:
    """Tests for CognitoService.create_user() method."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, cognito_service):
        """Test successful user registration."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "UserSub": "test-user-id-12345",
            "UserConfirmed": False,
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await cognito_service.create_user(
                email="newuser@test.com",
                password="Password123",
                name="New User",
                user_type="client"
            )

            assert result["user_id"] == "test-user-id-12345"
            assert result["username"] == "newuser"
            assert result["email"] == "newuser@test.com"

    @pytest.mark.asyncio
    async def test_create_user_with_secret_hash(self, cognito_service_with_secret):
        """Test create_user includes SECRET_HASH when client_secret is provided."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "UserSub": "test-user-id",
            "UserConfirmed": False,
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            await cognito_service_with_secret.create_user(
                email="newuser@test.com",
                password="Password123",
                name="New User",
                user_type="web"
            )

            # Verify SECRET_HASH was included in the request
            call_args = mock_post.call_args
            body = call_args.kwargs["json"]
            assert "SecretHash" in body

    @pytest.mark.asyncio
    async def test_create_user_already_exists(self, cognito_service):
        """Test create_user with existing email returns 409."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "__type": "UsernameExistsException",
            "message": "User already exists",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(HTTPException) as exc_info:
                await cognito_service.create_user(
                    email="existing@test.com",
                    password="Password123",
                    name="Existing User",
                    user_type="client"
                )

            assert exc_info.value.status_code == 409
            assert "already exists" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_user_invalid_password(self, cognito_service):
        """Test create_user with weak password returns 400."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "__type": "InvalidPasswordException",
            "message": "Password does not meet requirements",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(HTTPException) as exc_info:
                await cognito_service.create_user(
                    email="user@test.com",
                    password="weak",
                    name="User",
                    user_type="web"
                )

            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_create_user_cognito_service_unavailable(self, cognito_service):
        """Test create_user when Cognito service is down returns 503."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.NetworkError("Network error")
            )

            with pytest.raises(HTTPException) as exc_info:
                await cognito_service.create_user(
                    email="user@test.com",
                    password="Password123",
                    name="User",
                    user_type="seller"
                )

            assert exc_info.value.status_code == 503
            assert "temporarily unavailable" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_user_unknown_cognito_error(self, cognito_service):
        """Test create_user handles unexpected Cognito errors."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {
            "__type": "UnknownError",
            "message": "Something went wrong",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(HTTPException) as exc_info:
                await cognito_service.create_user(
                    email="user@test.com",
                    password="Password123",
                    name="User",
                    user_type="web"
                )

            assert exc_info.value.status_code == 500
            assert "Signup error" in exc_info.value.detail


class TestCognitoServiceDeleteUser:
    """Tests for CognitoService.delete_user() method."""

    @pytest.mark.asyncio
    async def test_delete_user_success(self, cognito_service):
        """Test successful user deletion."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            # Should not raise exception
            await cognito_service.delete_user("testuser")

            # Verify HTTP call was made correctly
            mock_post.assert_called_once()
            call_args = mock_post.call_args

            # Verify headers
            headers = call_args.kwargs["headers"]
            assert headers["X-Amz-Target"] == "AWSCognitoIdentityProviderService.AdminDeleteUser"

            # Verify body
            body = call_args.kwargs["json"]
            assert body["UserPoolId"] == "us-east-1_TestPool"
            assert body["Username"] == "testuser"

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, cognito_service):
        """Test delete_user with non-existent user returns 500."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "__type": "UserNotFoundException",
            "message": "User not found",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(HTTPException) as exc_info:
                await cognito_service.delete_user("nonexistent")

            assert exc_info.value.status_code == 500
            assert "Failed to delete user" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_delete_user_cognito_service_unavailable(self, cognito_service):
        """Test delete_user when Cognito service is down returns 503."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.ConnectError("Connection failed")
            )

            with pytest.raises(HTTPException) as exc_info:
                await cognito_service.delete_user("testuser")

            assert exc_info.value.status_code == 503
            assert "temporarily unavailable" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_delete_user_unknown_error(self, cognito_service):
        """Test delete_user handles unexpected errors."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {
            "__type": "InternalError",
            "message": "Something went wrong",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(HTTPException) as exc_info:
                await cognito_service.delete_user("testuser")

            assert exc_info.value.status_code == 500
            assert "Failed to delete user" in exc_info.value.detail


class TestCognitoServiceHelpers:
    """Tests for CognitoService helper methods."""

    def test_get_secret_hash_calculation(self, cognito_service_with_secret):
        """Test SECRET_HASH is computed correctly."""
        username = "testuser@example.com"
        secret_hash = cognito_service_with_secret._get_secret_hash(username)

        # Verify it's a valid base64 encoded string
        assert isinstance(secret_hash, str)
        assert len(secret_hash) > 0

        # Verify the calculation matches expected HMAC-SHA256
        message = bytes(username + "test-client-id", "utf-8")
        secret = bytes("test-client-secret", "utf-8")
        expected_hash = base64.b64encode(
            hmac.new(secret, message, hashlib.sha256).digest()
        ).decode()

        assert secret_hash == expected_hash

    def test_get_secret_hash_missing_secret(self, cognito_service):
        """Test SECRET_HASH raises error when client_secret is None."""
        with pytest.raises(ValueError) as exc_info:
            cognito_service._get_secret_hash("user@test.com")

        assert "Client secret is required" in str(exc_info.value)
