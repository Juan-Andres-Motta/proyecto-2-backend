"""Unit tests for authentication dependencies."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from jose.exceptions import JWTError

from common.auth.dependencies import (
    get_current_user,
    get_jwt_validator,
    require_client_user,
    require_groups,
    require_seller_user,
    require_web_user,
)


@pytest.fixture
def mock_credentials():
    """Fixture providing mock HTTP authorization credentials."""
    return HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="test-jwt-token"
    )


@pytest.fixture
def mock_user_claims():
    """Fixture providing mock user claims."""
    return {
        "sub": "user-123",
        "email": "test@example.com",
        "cognito:groups": ["web_users"],
        "custom:user_type": "web",
    }


class TestGetJWTValidator:
    """Tests for get_jwt_validator() function."""

    def test_get_jwt_validator_creates_instance(self):
        """Test JWT validator is created with correct parameters."""
        validator = get_jwt_validator(
            user_pool_id="test-pool",
            region="us-east-1",
            client_ids=("client-1", "client-2"),  # Must be tuple for lru_cache
        )

        assert validator.user_pool_id == "test-pool"
        assert validator.region == "us-east-1"
        # CognitoJWTValidator converts tuple to list internally
        assert validator.client_ids == ["client-1", "client-2"]

    def test_get_jwt_validator_caches_instance(self):
        """Test validator instance is cached for same parameters."""
        # Clear cache first
        get_jwt_validator.cache_clear()

        validator1 = get_jwt_validator(
            user_pool_id="test-pool",
            region="us-east-1",
            client_ids=("client-1",),  # Must be tuple for lru_cache
        )
        validator2 = get_jwt_validator(
            user_pool_id="test-pool",
            region="us-east-1",
            client_ids=("client-1",),
        )

        # Same instance due to caching
        assert validator1 is validator2


class TestGetCurrentUser:
    """Tests for get_current_user() dependency."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mock_credentials, mock_user_claims):
        """Test successful user authentication."""
        mock_validator = Mock()
        mock_validator.validate_token = AsyncMock(return_value=mock_user_claims)

        with patch(
            "common.auth.dependencies.get_jwt_validator", return_value=mock_validator
        ):
            with patch("common.auth.dependencies.settings") as mock_settings:
                mock_settings.aws_cognito_user_pool_id = "test-pool"
                mock_settings.aws_cognito_region = "us-east-1"
                mock_settings.aws_cognito_web_client_id = "web-client"
                mock_settings.aws_cognito_mobile_client_id = "mobile-client"

                result = await get_current_user(mock_credentials)

                assert result == mock_user_claims
                assert result["sub"] == "user-123"
                assert result["email"] == "test@example.com"
                mock_validator.validate_token.assert_called_once_with("test-jwt-token")

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, mock_credentials):
        """Test authentication fails for invalid token."""
        mock_validator = Mock()
        mock_validator.validate_token = AsyncMock(
            side_effect=JWTError("Invalid token")
        )

        with patch(
            "common.auth.dependencies.get_jwt_validator", return_value=mock_validator
        ):
            with patch("common.auth.dependencies.settings") as mock_settings:
                mock_settings.aws_cognito_user_pool_id = "test-pool"
                mock_settings.aws_cognito_region = "us-east-1"
                mock_settings.aws_cognito_web_client_id = "web-client"
                mock_settings.aws_cognito_mobile_client_id = "mobile-client"

                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(mock_credentials)

                assert exc_info.value.status_code == 401
                assert "Invalid authentication credentials" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self, mock_credentials):
        """Test authentication fails for expired token."""
        mock_validator = Mock()
        mock_validator.validate_token = AsyncMock(
            side_effect=JWTError("Signature has expired")
        )

        with patch(
            "common.auth.dependencies.get_jwt_validator", return_value=mock_validator
        ):
            with patch("common.auth.dependencies.settings") as mock_settings:
                mock_settings.aws_cognito_user_pool_id = "test-pool"
                mock_settings.aws_cognito_region = "us-east-1"
                mock_settings.aws_cognito_web_client_id = "web-client"
                mock_settings.aws_cognito_mobile_client_id = "mobile-client"

                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(mock_credentials)

                assert exc_info.value.status_code == 401


class TestRequireGroups:
    """Tests for require_groups() factory function."""

    @pytest.mark.asyncio
    async def test_require_groups_user_in_allowed_group(self):
        """Test access granted when user is in allowed group."""
        user = {"sub": "user-123", "cognito:groups": ["web_users"]}
        dependency = require_groups(["web_users"])

        # Mock get_current_user to return our test user
        with patch(
            "common.auth.dependencies.get_current_user", return_value=user
        ) as mock_get_user:
            result = await dependency(user)

            assert result == user

    @pytest.mark.asyncio
    async def test_require_groups_user_in_one_of_multiple_allowed_groups(self):
        """Test access granted when user is in one of multiple allowed groups."""
        user = {"sub": "user-123", "cognito:groups": ["seller_users"]}
        dependency = require_groups(["web_users", "seller_users"])

        result = await dependency(user)

        assert result == user

    @pytest.mark.asyncio
    async def test_require_groups_user_not_in_allowed_groups(self):
        """Test access denied when user not in allowed groups."""
        user = {"sub": "user-123", "cognito:groups": ["client_users"]}
        dependency = require_groups(["web_users", "seller_users"])

        with pytest.raises(HTTPException) as exc_info:
            await dependency(user)

        assert exc_info.value.status_code == 403
        assert "Access forbidden" in exc_info.value.detail
        assert "web_users, seller_users" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_groups_user_has_no_groups(self):
        """Test access denied when user has no groups."""
        user = {"sub": "user-123", "cognito:groups": []}
        dependency = require_groups(["web_users"])

        with pytest.raises(HTTPException) as exc_info:
            await dependency(user)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_groups_user_missing_groups_claim(self):
        """Test access denied when user JWT missing groups claim."""
        user = {"sub": "user-123"}  # No cognito:groups key
        dependency = require_groups(["web_users"])

        with pytest.raises(HTTPException) as exc_info:
            await dependency(user)

        assert exc_info.value.status_code == 403


class TestConvenienceDependencies:
    """Tests for convenience dependency functions."""

    @pytest.mark.asyncio
    async def test_require_web_user_success(self):
        """Test require_web_user allows web_users group."""
        user = {"sub": "user-123", "cognito:groups": ["web_users"]}

        result = await require_web_user(user)

        assert result == user

    @pytest.mark.asyncio
    async def test_require_web_user_rejects_other_groups(self):
        """Test require_web_user rejects non-web users."""
        user = {"sub": "user-123", "cognito:groups": ["seller_users"]}

        with pytest.raises(HTTPException) as exc_info:
            await require_web_user(user)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_seller_user_success(self):
        """Test require_seller_user allows seller_users group."""
        user = {"sub": "seller-123", "cognito:groups": ["seller_users"]}

        result = await require_seller_user(user)

        assert result == user

    @pytest.mark.asyncio
    async def test_require_seller_user_rejects_other_groups(self):
        """Test require_seller_user rejects non-seller users."""
        user = {"sub": "user-123", "cognito:groups": ["web_users"]}

        with pytest.raises(HTTPException) as exc_info:
            await require_seller_user(user)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_client_user_success(self):
        """Test require_client_user allows client_users group."""
        user = {"sub": "client-123", "cognito:groups": ["client_users"]}

        result = await require_client_user(user)

        assert result == user

    @pytest.mark.asyncio
    async def test_require_client_user_rejects_other_groups(self):
        """Test require_client_user rejects non-client users."""
        user = {"sub": "user-123", "cognito:groups": ["web_users"]}

        with pytest.raises(HTTPException) as exc_info:
            await require_client_user(user)

        assert exc_info.value.status_code == 403
