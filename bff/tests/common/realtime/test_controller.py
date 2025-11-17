"""Unit tests for Ably realtime token authentication controller."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException, status

from common.realtime.controller import (
    generate_token,
    get_token_service,
    _determine_user_type,
)
from common.realtime.token_service import AblyTokenService
from common.realtime.schemas import AblyTokenRequest, AblyTokenResponse


@pytest.fixture
def mock_token_service():
    """Create a mock AblyTokenService."""
    return Mock(spec=AblyTokenService)


@pytest.fixture
def sample_token_result():
    """Sample token result from token service."""
    token_request = AblyTokenRequest(
        keyName="test_key",
        clientId="test_client",
        ttl=3600000,
        timestamp=1640000000000,
        capability='{"web:user123":["subscribe"],"web:broadcasts":["subscribe"]}',
        nonce="abc123",
        mac="signature123"
    )
    return AblyTokenResponse(
        token_request=token_request,
        expires_at=1640003600000,
        channels=["web:user123", "web:broadcasts"]
    )


@pytest.fixture
def web_user():
    """Sample web user JWT claims."""
    return {
        "sub": "user123",
        "email": "user@example.com",
        "name": "Test User",
        "cognito:groups": ["web_users"],
        "custom:user_type": "web"
    }


@pytest.fixture
def seller_user():
    """Sample seller user JWT claims."""
    return {
        "sub": "seller456",
        "email": "seller@example.com",
        "name": "Test Seller",
        "cognito:groups": ["seller_users"],
        "custom:user_type": "seller"
    }


@pytest.fixture
def client_user():
    """Sample client user JWT claims."""
    return {
        "sub": "client789",
        "email": "client@hospital.com",
        "name": "Test Client",
        "cognito:groups": ["client_users"],
        "custom:user_type": "client"
    }


class TestDetermineUserType:
    """Tests for _determine_user_type() helper function."""

    def test_determine_user_type_from_custom_attribute(self):
        """Test extracts user type from custom:user_type attribute."""
        user = {
            "sub": "user123",
            "custom:user_type": "web",
            "cognito:groups": ["other_group"]
        }

        user_type = _determine_user_type(user)

        assert user_type == "web"

    def test_determine_user_type_from_web_users_group(self):
        """Test determines web type from cognito:groups."""
        user = {
            "sub": "user123",
            "cognito:groups": ["web_users"]
        }

        user_type = _determine_user_type(user)

        assert user_type == "web"

    def test_determine_user_type_from_seller_users_group(self):
        """Test determines seller type from cognito:groups."""
        user = {
            "sub": "user123",
            "cognito:groups": ["seller_users", "other_group"]
        }

        user_type = _determine_user_type(user)

        assert user_type == "seller"

    def test_determine_user_type_from_client_users_group(self):
        """Test determines client type from cognito:groups."""
        user = {
            "sub": "user123",
            "cognito:groups": ["client_users"]
        }

        user_type = _determine_user_type(user)

        assert user_type == "client"

    def test_determine_user_type_prefers_custom_attribute_over_groups(self):
        """Test custom:user_type takes precedence over groups."""
        user = {
            "sub": "user123",
            "custom:user_type": "web",
            "cognito:groups": ["seller_users"]
        }

        user_type = _determine_user_type(user)

        assert user_type == "web"

    def test_determine_user_type_raises_error_with_no_groups(self):
        """Test raises ValueError when no groups present."""
        user = {
            "sub": "user123",
            "cognito:groups": []
        }

        with pytest.raises(
            ValueError,
            match="Unable to determine user type from groups"
        ):
            _determine_user_type(user)

    def test_determine_user_type_raises_error_with_unknown_groups(self):
        """Test raises ValueError when groups don't match known types."""
        user = {
            "sub": "user123",
            "cognito:groups": ["unknown_group", "other_group"]
        }

        with pytest.raises(
            ValueError,
            match="Unable to determine user type from groups"
        ):
            _determine_user_type(user)

    def test_determine_user_type_handles_missing_groups_key(self):
        """Test handles missing cognito:groups key."""
        user = {
            "sub": "user123"
        }

        with pytest.raises(
            ValueError,
            match="Unable to determine user type from groups"
        ):
            _determine_user_type(user)


class TestGetTokenServiceDependency:
    """Tests for get_token_service() dependency."""

    @patch("common.realtime.controller.settings")
    def test_get_token_service_returns_service_instance(self, mock_settings):
        """Test creates and returns AblyTokenService instance."""
        mock_settings.ably_api_key = "test_key:test_secret"

        service = get_token_service()

        assert isinstance(service, AblyTokenService)
        assert service.api_key == "test_key:test_secret"

    @patch("common.realtime.controller.settings")
    def test_get_token_service_raises_503_when_api_key_missing(
        self, mock_settings
    ):
        """Test raises 503 when API key is not configured."""
        mock_settings.ably_api_key = ""

        with pytest.raises(HTTPException) as exc_info:
            get_token_service()

        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "Real-time service is not available" in exc_info.value.detail

    @patch("common.realtime.controller.settings")
    def test_get_token_service_raises_503_for_invalid_api_key_format(
        self, mock_settings
    ):
        """Test raises 503 when API key format is invalid."""
        mock_settings.ably_api_key = "invalid_key_without_colon"

        with pytest.raises(HTTPException) as exc_info:
            get_token_service()

        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "configuration error" in exc_info.value.detail


class TestGenerateTokenEndpoint:
    """Tests for /auth/ably/token endpoint."""

    @pytest.mark.asyncio
    async def test_generate_token_for_web_user(
        self, web_user, mock_token_service, sample_token_result
    ):
        """Test token generation for web user."""
        mock_token_service.generate_token_request = AsyncMock(
            return_value=sample_token_result
        )

        result = await generate_token(web_user, mock_token_service)

        mock_token_service.generate_token_request.assert_called_once_with(
            user_id="user123",
            user_type="web",
            client_id="user@example.com",
            ttl=3600000
        )

        assert isinstance(result, AblyTokenResponse)
        assert result.token_request == sample_token_result.token_request
        assert result.expires_at == sample_token_result.expires_at
        assert result.channels == sample_token_result.channels

    @pytest.mark.asyncio
    async def test_generate_token_for_seller_user(
        self, seller_user, mock_token_service
    ):
        """Test token generation for seller user."""
        token_request = AblyTokenRequest(
            keyName="test_key",
        clientId="test_client",
            ttl=3600000,
            timestamp=1640000000000,
            capability='{"mobile:products":["subscribe"]}',
            nonce="test_nonce",
            mac="test_mac"
        )
        seller_token_result = AblyTokenResponse(
            token_request=token_request,
            expires_at=1640003600000,
            channels=["mobile:products"]
        )
        mock_token_service.generate_token_request = AsyncMock(
            return_value=seller_token_result
        )

        result = await generate_token(seller_user, mock_token_service)

        mock_token_service.generate_token_request.assert_called_once_with(
            user_id="seller456",
            user_type="seller",
            client_id="seller@example.com",
            ttl=3600000
        )

        assert isinstance(result, AblyTokenResponse)
        assert result.channels == ["mobile:products"]

    @pytest.mark.asyncio
    async def test_generate_token_for_client_user(
        self, client_user, mock_token_service
    ):
        """Test token generation for client user."""
        token_request = AblyTokenRequest(
            keyName="test_key",
        clientId="test_client",
            ttl=3600000,
            timestamp=1640000000000,
            capability='{"mobile:products":["subscribe"]}',
            nonce="test_nonce",
            mac="test_mac"
        )
        client_token_result = AblyTokenResponse(
            token_request=token_request,
            expires_at=1640003600000,
            channels=["mobile:products"]
        )
        mock_token_service.generate_token_request = AsyncMock(
            return_value=client_token_result
        )

        result = await generate_token(client_user, mock_token_service)

        mock_token_service.generate_token_request.assert_called_once_with(
            user_id="client789",
            user_type="client",
            client_id="client@hospital.com",
            ttl=3600000
        )

        assert isinstance(result, AblyTokenResponse)

    @pytest.mark.asyncio
    async def test_generate_token_uses_user_id_when_email_missing(
        self, mock_token_service, sample_token_result
    ):
        """Test uses user_id as client_id when email is not present."""
        user = {
            "sub": "user123",
            "cognito:groups": ["web_users"]
        }
        mock_token_service.generate_token_request = AsyncMock(
            return_value=sample_token_result
        )

        await generate_token(user, mock_token_service)

        mock_token_service.generate_token_request.assert_called_once_with(
            user_id="user123",
            user_type="web",
            client_id="user123",
            ttl=3600000
        )

    @pytest.mark.asyncio
    async def test_generate_token_determines_user_type_from_groups(
        self, mock_token_service, sample_token_result
    ):
        """Test determines user type from cognito:groups when custom attribute missing."""
        user = {
            "sub": "user123",
            "email": "user@example.com",
            "cognito:groups": ["seller_users"]
        }
        token_request = AblyTokenRequest(
            keyName="test_key",
        clientId="test_client",
            ttl=3600000,
            timestamp=1640000000000,
            capability='{"mobile:products":["subscribe"]}',
            nonce="test_nonce",
            mac="test_mac"
        )
        seller_token_result = AblyTokenResponse(
            token_request=token_request,
            expires_at=1640003600000,
            channels=["mobile:products"]
        )
        mock_token_service.generate_token_request = AsyncMock(
            return_value=seller_token_result
        )

        await generate_token(user, mock_token_service)

        call_args = mock_token_service.generate_token_request.call_args
        assert call_args[1]["user_type"] == "seller"

    @pytest.mark.asyncio
    async def test_generate_token_raises_400_when_user_id_missing(
        self, mock_token_service
    ):
        """Test raises 400 when user_id (sub) is missing from token."""
        user = {
            "email": "user@example.com",
            "cognito:groups": ["web_users"]
        }

        with pytest.raises(HTTPException) as exc_info:
            await generate_token(user, mock_token_service)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "User ID missing" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_generate_token_raises_400_when_user_type_cannot_be_determined(
        self, mock_token_service
    ):
        """Test raises 400 when user type cannot be determined."""
        user = {
            "sub": "user123",
            "email": "user@example.com",
            "cognito:groups": ["unknown_group"]
        }

        with pytest.raises(HTTPException) as exc_info:
            await generate_token(user, mock_token_service)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Unable to determine user type" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_generate_token_raises_400_for_invalid_parameters(
        self, web_user, mock_token_service
    ):
        """Test raises 400 when token service raises ValueError."""
        mock_token_service.generate_token_request = AsyncMock(
            side_effect=ValueError("Invalid user_type")
        )

        with pytest.raises(HTTPException) as exc_info:
            await generate_token(web_user, mock_token_service)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid request" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_generate_token_raises_503_on_service_error(
        self, web_user, mock_token_service
    ):
        """Test raises 503 when token service fails."""
        mock_token_service.generate_token_request = AsyncMock(
            side_effect=Exception("Ably connection failed")
        )

        with pytest.raises(HTTPException) as exc_info:
            await generate_token(web_user, mock_token_service)

        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "Failed to generate token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_generate_token_uses_1_hour_ttl(
        self, web_user, mock_token_service, sample_token_result
    ):
        """Test always uses 1 hour (3600000ms) TTL."""
        mock_token_service.generate_token_request = AsyncMock(
            return_value=sample_token_result
        )

        await generate_token(web_user, mock_token_service)

        call_args = mock_token_service.generate_token_request.call_args
        assert call_args[1]["ttl"] == 3600000


class TestEndpointIntegration:
    """Integration tests for the endpoint with real dependencies."""

    @pytest.mark.asyncio
    async def test_endpoint_returns_correct_response_model(
        self, web_user, mock_token_service, sample_token_result
    ):
        """Test endpoint returns properly structured AblyTokenResponse."""
        mock_token_service.generate_token_request = AsyncMock(
            return_value=sample_token_result
        )

        result = await generate_token(web_user, mock_token_service)

        # Verify response has all required fields
        assert hasattr(result, "token_request")
        assert hasattr(result, "expires_at")
        assert hasattr(result, "channels")

        # Verify token_request structure
        assert hasattr(result.token_request, "keyName")
        assert hasattr(result.token_request, "ttl")
        assert hasattr(result.token_request, "capability")

        # Verify expires_at is a positive integer
        assert isinstance(result.expires_at, int)
        assert result.expires_at > 0

        # Verify channels is a list
        assert isinstance(result.channels, list)
        assert len(result.channels) > 0

    @pytest.mark.asyncio
    async def test_endpoint_logs_token_generation(
        self, web_user, mock_token_service, sample_token_result, caplog
    ):
        """Test endpoint logs token generation events."""
        import logging
        # Set log level to capture INFO logs
        caplog.set_level(logging.INFO)

        mock_token_service.generate_token_request = AsyncMock(
            return_value=sample_token_result
        )

        await generate_token(web_user, mock_token_service)

        # Verify logging occurred
        assert "Token request for user" in caplog.text or "Successfully generated token for user" in caplog.text
        assert "user123" in caplog.text

    @pytest.mark.asyncio
    async def test_endpoint_handles_all_user_types(
        self, mock_token_service
    ):
        """Test endpoint works with all supported user types."""
        users = [
            {"sub": "u1", "email": "u1@test.com", "cognito:groups": ["web_users"]},
            {"sub": "u2", "email": "u2@test.com", "cognito:groups": ["seller_users"]},
            {"sub": "u3", "email": "u3@test.com", "cognito:groups": ["client_users"]},
        ]

        for user in users:
            token_request = AblyTokenRequest(
                keyName="test_key",
        clientId="test_client",
                ttl=3600000,
                timestamp=1640000000000,
                capability='{}',
                nonce="test_nonce",
                mac="test_mac"
            )
            test_token_result = AblyTokenResponse(
                token_request=token_request,
                expires_at=1640003600000,
                channels=["test:channel"]
            )
            mock_token_service.generate_token_request = AsyncMock(
                return_value=test_token_result
            )

            result = await generate_token(user, mock_token_service)
            assert isinstance(result, AblyTokenResponse)
