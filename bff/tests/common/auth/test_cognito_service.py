"""Unit tests for CognitoService."""

import base64
import hashlib
import hmac
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from botocore.exceptions import ClientError
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
        """Test successful user registration via AdminCreateUser."""
        mock_client = AsyncMock()
        mock_admin_create_user = AsyncMock(return_value={
            "User": {
                "Username": "newuser",
                "Attributes": [
                    {"Name": "sub", "Value": "test-user-id-12345"},
                    {"Name": "email", "Value": "newuser@test.com"},
                    {"Name": "name", "Value": "New User"},
                    {"Name": "custom:user_type", "Value": "client"},
                ]
            }
        })
        mock_admin_set_user_password = AsyncMock()
        mock_client.admin_create_user = mock_admin_create_user
        mock_client.admin_set_user_password = mock_admin_set_user_password

        with patch("aioboto3.Session") as mock_session:
            mock_session.return_value.client.return_value.__aenter__.return_value = mock_client

            result = await cognito_service.create_user(
                email="newuser@test.com",
                password="Password123",
                name="New User",
                user_type="client"
            )

            assert result["user_id"] == "test-user-id-12345"
            assert result["username"] == "newuser"
            assert result["email"] == "newuser@test.com"

            # Verify admin_set_user_password was called with permanent password
            mock_admin_set_user_password.assert_called_once_with(
                UserPoolId="us-east-1_TestPool",
                Username="newuser",
                Password="Password123",
                Permanent=True
            )

    @pytest.mark.asyncio
    async def test_create_user_with_secret_hash(self, cognito_service_with_secret):
        """Test create_user via AdminCreateUser (SECRET_HASH no longer needed for admin operations)."""
        mock_client = AsyncMock()
        mock_admin_create_user = AsyncMock(return_value={
            "User": {
                "Username": "newuser",
                "Attributes": [
                    {"Name": "sub", "Value": "test-user-id"},
                    {"Name": "email", "Value": "newuser@test.com"},
                ]
            }
        })
        mock_admin_set_user_password = AsyncMock()
        mock_client.admin_create_user = mock_admin_create_user
        mock_client.admin_set_user_password = mock_admin_set_user_password

        with patch("aioboto3.Session") as mock_session:
            mock_session.return_value.client.return_value.__aenter__.return_value = mock_client

            result = await cognito_service_with_secret.create_user(
                email="newuser@test.com",
                password="Password123",
                name="New User",
                user_type="web"
            )

            # Verify admin_create_user was called with correct parameters
            mock_admin_create_user.assert_called_once()
            create_call = mock_admin_create_user.call_args
            assert create_call.kwargs["UserPoolId"] == "us-east-1_TestPool"
            assert create_call.kwargs["Username"] == "newuser"

            # Verify admin_set_user_password was called
            mock_admin_set_user_password.assert_called_once()
            password_call = mock_admin_set_user_password.call_args
            assert password_call.kwargs["Password"] == "Password123"
            assert password_call.kwargs["Permanent"] is True

            assert result["user_id"] == "test-user-id"

    @pytest.mark.asyncio
    async def test_create_user_already_exists(self, cognito_service):
        """Test create_user with existing email returns 409 (UsernameExistsException)."""
        mock_client = AsyncMock()
        error_response = {
            "Error": {
                "Code": "UsernameExistsException",
                "Message": "User already exists"
            }
        }
        mock_client.admin_create_user = AsyncMock(
            side_effect=ClientError(error_response, "AdminCreateUser")
        )

        with patch("aioboto3.Session") as mock_session:
            mock_session.return_value.client.return_value.__aenter__.return_value = mock_client

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
        """Test create_user with weak password returns 400 (InvalidPasswordException)."""
        mock_client = AsyncMock()
        error_response = {
            "Error": {
                "Code": "InvalidPasswordException",
                "Message": "Password does not meet requirements"
            }
        }
        mock_client.admin_create_user = AsyncMock(
            side_effect=ClientError(error_response, "AdminCreateUser")
        )

        with patch("aioboto3.Session") as mock_session:
            mock_session.return_value.client.return_value.__aenter__.return_value = mock_client

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
        """Test create_user when Cognito service is down returns 503 (generic Exception)."""
        mock_client = AsyncMock()
        mock_client.admin_create_user = AsyncMock(
            side_effect=Exception("Connection failed")
        )

        with patch("aioboto3.Session") as mock_session:
            mock_session.return_value.client.return_value.__aenter__.return_value = mock_client

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
        """Test create_user handles unexpected AWS ClientError (500 error)."""
        mock_client = AsyncMock()
        error_response = {
            "Error": {
                "Code": "InternalServerError",
                "Message": "Something went wrong"
            }
        }
        mock_client.admin_create_user = AsyncMock(
            side_effect=ClientError(error_response, "AdminCreateUser")
        )

        with patch("aioboto3.Session") as mock_session:
            mock_session.return_value.client.return_value.__aenter__.return_value = mock_client

            with pytest.raises(HTTPException) as exc_info:
                await cognito_service.create_user(
                    email="user@test.com",
                    password="Password123",
                    name="User",
                    user_type="web"
                )

            assert exc_info.value.status_code == 500


class TestCognitoServiceDeleteUser:
    """Tests for CognitoService.delete_user() method."""

    @pytest.mark.asyncio
    async def test_delete_user_success(self, cognito_service):
        """Test successful user deletion."""
        mock_client = AsyncMock()
        mock_admin_delete_user = AsyncMock()
        mock_client.admin_delete_user = mock_admin_delete_user

        with patch("aioboto3.Session") as mock_session:
            mock_session.return_value.client.return_value.__aenter__.return_value = mock_client

            # Should not raise exception
            await cognito_service.delete_user("testuser")

            # Verify admin_delete_user was called correctly
            mock_admin_delete_user.assert_called_once_with(
                UserPoolId="us-east-1_TestPool",
                Username="testuser"
            )

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, cognito_service):
        """Test delete_user with non-existent user returns 500 (UserNotFoundException)."""
        mock_client = AsyncMock()
        error_response = {
            "Error": {
                "Code": "UserNotFoundException",
                "Message": "User not found"
            }
        }
        mock_client.admin_delete_user = AsyncMock(
            side_effect=ClientError(error_response, "AdminDeleteUser")
        )

        with patch("aioboto3.Session") as mock_session:
            mock_session.return_value.client.return_value.__aenter__.return_value = mock_client

            with pytest.raises(HTTPException) as exc_info:
                await cognito_service.delete_user("nonexistent")

            assert exc_info.value.status_code == 500
            assert "Failed to delete user" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_delete_user_cognito_service_unavailable(self, cognito_service):
        """Test delete_user when Cognito service is down returns 503."""
        with patch("aioboto3.Session") as mock_session:
            mock_client = AsyncMock()
            mock_client.admin_delete_user = AsyncMock(
                side_effect=Exception("Connection failed")
            )
            mock_session.return_value.client.return_value.__aenter__.return_value = mock_client

            with pytest.raises(HTTPException) as exc_info:
                await cognito_service.delete_user("testuser")

            assert exc_info.value.status_code == 503
            assert "temporarily unavailable" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_delete_user_unknown_error(self, cognito_service):
        """Test delete_user handles unexpected AWS ClientError."""
        mock_client = AsyncMock()
        error_response = {
            "Error": {
                "Code": "InternalServerError",
                "Message": "Something went wrong"
            }
        }
        mock_client.admin_delete_user = AsyncMock(
            side_effect=ClientError(error_response, "AdminDeleteUser")
        )

        with patch("aioboto3.Session") as mock_session:
            mock_session.return_value.client.return_value.__aenter__.return_value = mock_client

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


class TestCognitoServiceAddUserToGroup:
    """Tests for add_user_to_group method."""

    @pytest.fixture
    def cognito_service(self):
        """Fixture providing CognitoService instance."""
        return CognitoService(
            user_pool_id="us-east-1_TestPool",
            client_id="test-client-id",
            client_secret=None,
            region="us-east-1",
        )

    @pytest.mark.asyncio
    async def test_add_user_to_group_success(self, cognito_service):
        """Test adding user to group successfully."""
        with patch("aioboto3.Session") as mock_session:
            mock_client = AsyncMock()
            mock_session.return_value.client.return_value.__aenter__.return_value = mock_client
            mock_client.admin_add_user_to_group = AsyncMock()

            await cognito_service.add_user_to_group("testuser", "seller_users")

            mock_client.admin_add_user_to_group.assert_called_once_with(
                UserPoolId="us-east-1_TestPool",
                Username="testuser",
                GroupName="seller_users",
            )

    @pytest.mark.asyncio
    async def test_add_user_to_group_test_mode(self, cognito_service):
        """Test add_user_to_group is skipped in TEST_MODE."""
        import os

        with patch.dict(os.environ, {"TEST_MODE": "true"}):
            # Should not raise any errors and should not call AWS
            await cognito_service.add_user_to_group("testuser", "seller_users")

    @pytest.mark.asyncio
    async def test_add_user_to_group_not_found(self, cognito_service):
        """Test adding non-existent user to group."""
        with patch("aioboto3.Session") as mock_session:
            mock_client = AsyncMock()
            mock_session.return_value.client.return_value.__aenter__.return_value = mock_client

            error_response = {"Error": {"Code": "UserNotFoundException", "Message": "User not found"}}
            mock_client.admin_add_user_to_group = AsyncMock(
                side_effect=ClientError(error_response, "AdminAddUserToGroup")
            )

            with pytest.raises(HTTPException) as exc_info:
                await cognito_service.add_user_to_group("nonexistent", "seller_users")

            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_add_user_to_group_cognito_error(self, cognito_service):
        """Test add_user_to_group handles Cognito errors."""
        with patch("aioboto3.Session") as mock_session:
            mock_client = AsyncMock()
            mock_session.return_value.client.return_value.__aenter__.return_value = mock_client

            error_response = {"Error": {"Code": "InternalErrorException", "Message": "Internal error"}}
            mock_client.admin_add_user_to_group = AsyncMock(
                side_effect=ClientError(error_response, "AdminAddUserToGroup")
            )

            with pytest.raises(HTTPException) as exc_info:
                await cognito_service.add_user_to_group("testuser", "seller_users")

            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_add_user_to_group_unexpected_error(self, cognito_service):
        """Test add_user_to_group handles unexpected errors."""
        with patch("aioboto3.Session") as mock_session:
            mock_client = AsyncMock()
            mock_session.return_value.client.return_value.__aenter__.return_value = mock_client
            mock_client.admin_add_user_to_group = AsyncMock(
                side_effect=Exception("Unexpected error")
            )

            with pytest.raises(HTTPException) as exc_info:
                await cognito_service.add_user_to_group("testuser", "seller_users")

            assert exc_info.value.status_code == 503


class TestCognitoServiceTestMode:
    """Tests for TEST_MODE functionality."""

    @pytest.fixture
    def cognito_service(self):
        """Fixture providing CognitoService instance."""
        return CognitoService(
            user_pool_id="us-east-1_TestPool",
            client_id="test-client-id",
            client_secret=None,
            region="us-east-1",
        )

    @pytest.mark.asyncio
    async def test_login_test_mode_returns_mock_tokens(self, cognito_service):
        """Test login returns mock tokens in TEST_MODE."""
        import os

        with patch.dict(os.environ, {"TEST_MODE": "true"}):
            result = await cognito_service.login("seller@test.com", "anypassword")

            assert "access_token" in result
            assert "id_token" in result
            assert "refresh_token" in result
            assert result["expires_in"] == 3600

    @pytest.mark.asyncio
    async def test_create_user_test_mode_returns_mock_user(self, cognito_service):
        """Test create_user returns mock user in TEST_MODE."""
        import os

        with patch.dict(os.environ, {"TEST_MODE": "true"}):
            result = await cognito_service.create_user(
                "client@test.com", "Password123", "Test User", "client"
            )

            assert "user_id" in result
            assert result["username"] == "client"
            assert result["email"] == "client@test.com"

    @pytest.mark.asyncio
    async def test_delete_user_test_mode_is_skipped(self, cognito_service):
        """Test delete_user is skipped in TEST_MODE."""
        import os

        with patch.dict(os.environ, {"TEST_MODE": "true"}):
            # Should not raise any errors
            await cognito_service.delete_user("testuser")


class TestCognitoServiceLocalStackEndpoint:
    """Tests for LocalStack endpoint handling."""

    def test_init_uses_localstack_endpoint_when_set(self, monkeypatch):
        """Test uses LocalStack endpoint when AWS_ENDPOINT_URL is set."""
        monkeypatch.setenv("AWS_ENDPOINT_URL", "http://localhost:4566")

        service = CognitoService(
            user_pool_id="us-east-1_TestPool",
            client_id="test-client-id",
            client_secret=None,
            region="us-east-1",
        )

        assert service.cognito_idp_url == "http://localhost:4566/"

    def test_init_uses_real_aws_when_endpoint_not_set(self):
        """Test uses real AWS endpoint when AWS_ENDPOINT_URL not set."""
        service = CognitoService(
            user_pool_id="us-east-1_TestPool",
            client_id="test-client-id",
            client_secret=None,
            region="us-east-1",
        )

        assert "cognito-idp" in service.cognito_idp_url
        assert "amazonaws.com" in service.cognito_idp_url
