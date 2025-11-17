"""Unit tests for AblyTokenService."""

import json
import time
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock

from common.realtime.token_service import AblyTokenService
from common.realtime.schemas import AblyTokenRequest, AblyTokenResponse


class TestAblyTokenServiceInit:
    """Tests for AblyTokenService initialization."""

    def test_init_stores_configuration(self):
        """Test constructor stores API key."""
        service = AblyTokenService(
            api_key="test_key:test_secret"
        )

        assert service.api_key == "test_key:test_secret"
        assert service._client is None

    def test_init_raises_error_with_empty_api_key(self):
        """Test raises ValueError when API key is empty."""
        with pytest.raises(ValueError, match="Ably API key is required"):
            AblyTokenService(api_key="")

    def test_init_raises_error_with_invalid_api_key_format(self):
        """Test raises ValueError when API key format is invalid."""
        with pytest.raises(
            ValueError,
            match="Ably API key must be in format 'key_id:key_secret'"
        ):
            AblyTokenService(api_key="invalid_key_without_colon")

    def test_init_accepts_valid_api_key_format(self):
        """Test accepts API key in correct format."""
        service = AblyTokenService(api_key="key_id:key_secret")
        assert service.api_key == "key_id:key_secret"


class TestAblyTokenServiceGetClient:
    """Tests for _get_client() lazy loading."""

    def test_get_client_creates_ably_rest_client(self):
        """Test client is created with correct API key."""
        with patch("ably.AblyRest") as mock_ably_rest:
            service = AblyTokenService(api_key="test_key:test_secret")

            client = service._get_client()

            mock_ably_rest.assert_called_once_with("test_key:test_secret")
            assert client == mock_ably_rest.return_value

    def test_get_client_caches_instance(self):
        """Test client is only created once."""
        with patch("ably.AblyRest") as mock_ably_rest:
            service = AblyTokenService(api_key="test_key:test_secret")

            client1 = service._get_client()
            client2 = service._get_client()

            assert mock_ably_rest.call_count == 1
            assert client1 is client2

    def test_get_client_raises_import_error_if_ably_not_installed(self):
        """Test raises ImportError if ably package not installed."""
        service = AblyTokenService(api_key="test_key:test_secret")

        # Mock the import to raise ImportError
        import sys
        original_modules = sys.modules.copy()

        # Remove ably from sys.modules if it exists
        if 'ably' in sys.modules:
            del sys.modules['ably']

        try:
            # Add a fake ably module that raises ImportError when accessed
            class FakeAblyModule:
                def __getattr__(self, name):
                    raise ImportError("No module named 'ably'")

            sys.modules['ably'] = FakeAblyModule()

            with pytest.raises(ImportError):
                service._get_client()
        finally:
            # Restore original modules
            sys.modules.clear()
            sys.modules.update(original_modules)

    def test_get_client_raises_exception_on_client_initialization_failure(self):
        """Test raises exception when Ably client initialization fails."""
        service = AblyTokenService(api_key="test_key:test_secret")

        with patch("ably.AblyRest", side_effect=Exception("Connection failed")):
            with pytest.raises(Exception, match="Connection failed"):
                service._get_client()


class TestAblyTokenServiceBuildCapabilities:
    """Tests for _build_capabilities() method."""

    def test_build_capabilities_for_web_user(self):
        """Test capabilities for web user type."""
        service = AblyTokenService(
            api_key="test_key:test_secret"
        )

        capabilities = service._build_capabilities(
            user_id="user123",
            user_type="web"
        )

        assert capabilities == {
            "web:user123": ["subscribe"],
            "web:broadcasts": ["subscribe"]
        }

    def test_build_capabilities_for_seller_user(self):
        """Test capabilities for seller user type."""
        service = AblyTokenService(
            api_key="test_key:test_secret"
        )

        capabilities = service._build_capabilities(
            user_id="seller456",
            user_type="seller"
        )

        assert capabilities == {
            "mobile:products": ["subscribe"]
        }

    def test_build_capabilities_for_client_user(self):
        """Test capabilities for client user type."""
        service = AblyTokenService(
            api_key="test_key:test_secret"
        )

        capabilities = service._build_capabilities(
            user_id="client789",
            user_type="client"
        )

        assert capabilities == {
            "mobile:products": ["subscribe"]
        }

    def test_build_capabilities_for_unknown_user_type(self):
        """Test capabilities for unknown user type returns empty dict."""
        service = AblyTokenService(
            api_key="test_key:test_secret"
        )

        capabilities = service._build_capabilities(
            user_id="user123",
            user_type="unknown"
        )

        assert capabilities == {}



class TestAblyTokenServiceGenerateTokenRequest:
    """Tests for generate_token_request() method."""

    @patch("ably.AblyRest")
    @patch("time.time")
    async def test_generate_token_request_for_web_user(
        self, mock_time, mock_ably_rest
    ):
        """Test token generation for web user."""
        # Setup mocks
        mock_time.return_value = 1640000000.0  # 2021-12-20 12:26:40 UTC
        mock_client = Mock()
        mock_auth = Mock()
        mock_ably_rest.return_value = mock_client
        mock_client.auth = mock_auth

        # Mock Ably's TokenRequest object with attributes
        mock_token_request_obj = Mock()
        mock_token_request_obj.key_name = "test_key"
        mock_token_request_obj.client_id = "test_client"
        mock_token_request_obj.ttl = 3600000
        mock_token_request_obj.timestamp = 1640000000000
        mock_token_request_obj.capability = '{"web:user123":["subscribe"],"web:broadcasts":["subscribe"]}'
        mock_token_request_obj.nonce = "abc123"
        mock_token_request_obj.mac = "signature123"
        mock_auth.create_token_request = AsyncMock(return_value=mock_token_request_obj)

        # Execute
        service = AblyTokenService(
            api_key="test_key:test_secret"
        )
        result = await service.generate_token_request(
            user_id="user123",
            user_type="web",
            client_id="user123@example.com",
            ttl=3600000
        )

        # Verify
        expected_capability = json.dumps({
            "web:user123": ["subscribe"],
            "web:broadcasts": ["subscribe"]
        }, separators=(',', ':'))
        mock_auth.create_token_request.assert_called_once_with({
            "client_id": "user123@example.com",
            "ttl": 3600000,
            "capability": expected_capability
        })

        # Result should be an AblyTokenResponse
        assert isinstance(result, AblyTokenResponse)
        assert isinstance(result.token_request, AblyTokenRequest)
        assert result.token_request.keyName == "test_key"
        assert result.token_request.ttl == 3600000
        assert result.token_request.timestamp == 1640000000000
        assert result.token_request.nonce == "abc123"
        assert result.token_request.mac == "signature123"
        assert result.expires_at == 1640003600000  # current + ttl
        assert set(result.channels) == {"web:user123", "web:broadcasts"}

    @patch("ably.AblyRest")
    @patch("time.time")
    async def test_generate_token_request_for_seller_user(
        self, mock_time, mock_ably_rest
    ):
        """Test token generation for seller user."""
        # Setup mocks
        mock_time.return_value = 1640000000.0
        mock_client = Mock()
        mock_auth = Mock()
        mock_ably_rest.return_value = mock_client
        mock_client.auth = mock_auth

        mock_token_request_obj = Mock()
        mock_token_request_obj.key_name = "test_key"
        mock_token_request_obj.client_id = "test_client"
        mock_token_request_obj.ttl = 3600000
        mock_token_request_obj.timestamp = 1640000000000
        mock_token_request_obj.capability = '{"mobile:products":["subscribe"]}'
        mock_token_request_obj.nonce = "def456"
        mock_token_request_obj.mac = "signature456"
        mock_auth.create_token_request = AsyncMock(return_value=mock_token_request_obj)

        # Execute
        service = AblyTokenService(
            api_key="test_key:test_secret"
        )
        result = await service.generate_token_request(
            user_id="seller123",
            user_type="seller",
            ttl=3600000
        )

        # Verify
        expected_capability = json.dumps({
            "mobile:products": ["subscribe"]
        }, separators=(',', ':'))
        mock_auth.create_token_request.assert_called_once_with({
            "client_id": "seller123",
            "ttl": 3600000,
            "capability": expected_capability
        })

        assert isinstance(result, AblyTokenResponse)
        assert result.channels == ["mobile:products"]

    @patch("ably.AblyRest")
    @patch("time.time")
    async def test_generate_token_request_for_client_user(
        self, mock_time, mock_ably_rest
    ):
        """Test token generation for client user."""
        # Setup mocks
        mock_time.return_value = 1640000000.0
        mock_client = Mock()
        mock_auth = Mock()
        mock_ably_rest.return_value = mock_client
        mock_client.auth = mock_auth

        mock_token_request_obj = Mock()
        mock_token_request_obj.key_name = "test_key"
        mock_token_request_obj.client_id = "test_client"
        mock_token_request_obj.ttl = 3600000
        mock_token_request_obj.timestamp = 1640000000000
        mock_token_request_obj.capability = '{"mobile:products":["subscribe"]}'
        mock_token_request_obj.nonce = "ghi789"
        mock_token_request_obj.mac = "signature789"
        mock_auth.create_token_request = AsyncMock(return_value=mock_token_request_obj)

        # Execute
        service = AblyTokenService(
            api_key="test_key:test_secret"
        )
        result = await service.generate_token_request(
            user_id="client123",
            user_type="client",
            ttl=3600000
        )

        # Verify
        assert isinstance(result, AblyTokenResponse)
        assert result.channels == ["mobile:products"]

    @patch("ably.AblyRest")
    async def test_generate_token_request_uses_user_id_as_default_client_id(
        self, mock_ably_rest
    ):
        """Test uses user_id as client_id when not provided."""
        mock_client = Mock()
        mock_auth = Mock()
        mock_ably_rest.return_value = mock_client
        mock_client.auth = mock_auth

        mock_token_request_obj = Mock()
        mock_token_request_obj.key_name = "test_key"
        mock_token_request_obj.client_id = "test_client"
        mock_token_request_obj.ttl = 3600000
        mock_token_request_obj.timestamp = 1640000000000
        mock_token_request_obj.capability = '{}'
        mock_token_request_obj.nonce = "test_nonce"
        mock_token_request_obj.mac = "test_mac"
        mock_auth.create_token_request = AsyncMock(return_value=mock_token_request_obj)

        service = AblyTokenService(api_key="test_key:test_secret")
        await service.generate_token_request(
            user_id="user123",
            user_type="web"
        )

        call_args = mock_auth.create_token_request.call_args[0][0]
        assert call_args["client_id"] == "user123"

    async def test_generate_token_request_raises_error_for_empty_user_id(self):
        """Test raises ValueError when user_id is empty."""
        service = AblyTokenService(api_key="test_key:test_secret")

        with pytest.raises(ValueError, match="user_id is required"):
            await service.generate_token_request(
                user_id="",
                user_type="web"
            )

    async def test_generate_token_request_raises_error_for_empty_user_type(self):
        """Test raises ValueError when user_type is empty."""
        service = AblyTokenService(api_key="test_key:test_secret")

        with pytest.raises(ValueError, match="user_type is required"):
            await service.generate_token_request(
                user_id="user123",
                user_type=""
            )

    async def test_generate_token_request_raises_error_for_invalid_user_type(self):
        """Test raises ValueError for invalid user_type."""
        service = AblyTokenService(api_key="test_key:test_secret")

        with pytest.raises(
            ValueError,
            match="Invalid user_type: admin. Must be one of: web, seller, client"
        ):
            await service.generate_token_request(
                user_id="user123",
                user_type="admin"
            )

    async def test_generate_token_request_raises_error_for_empty_capabilities(self):
        """Test raises ValueError when no capabilities can be determined."""
        service = AblyTokenService(api_key="test_key:test_secret")

        # Monkey-patch _build_capabilities to return empty dict
        original_build = service._build_capabilities
        service._build_capabilities = lambda user_id, user_type: {}

        try:
            with pytest.raises(
                ValueError,
                match="No capabilities could be determined for user_type"
            ):
                await service.generate_token_request(
                    user_id="user123",
                    user_type="web"
                )
        finally:
            # Restore original method
            service._build_capabilities = original_build

    @patch("ably.AblyRest")
    async def test_generate_token_request_handles_ably_errors(self, mock_ably_rest):
        """Test handles errors from Ably SDK."""
        mock_client = Mock()
        mock_auth = Mock()
        mock_ably_rest.return_value = mock_client
        mock_client.auth = mock_auth
        mock_auth.create_token_request.side_effect = Exception("Ably error")

        service = AblyTokenService(api_key="test_key:test_secret")

        with pytest.raises(Exception, match="Ably error"):
            await service.generate_token_request(
                user_id="user123",
                user_type="web"
            )

    @patch("ably.AblyRest")
    @patch("time.time")
    async def test_generate_token_request_calculates_expiration_correctly(
        self, mock_time, mock_ably_rest
    ):
        """Test expiration timestamp is calculated correctly."""
        mock_time.return_value = 1640000000.0  # 1640000000000 ms
        mock_client = Mock()
        mock_auth = Mock()
        mock_ably_rest.return_value = mock_client
        mock_client.auth = mock_auth

        mock_token_request_obj = Mock()
        mock_token_request_obj.key_name = "test_key"
        mock_token_request_obj.client_id = "test_client"
        mock_token_request_obj.ttl = 7200000
        mock_token_request_obj.timestamp = 1640000000000
        mock_token_request_obj.capability = '{}'
        mock_token_request_obj.nonce = "test_nonce"
        mock_token_request_obj.mac = "test_mac"
        mock_auth.create_token_request = AsyncMock(return_value=mock_token_request_obj)

        service = AblyTokenService(api_key="test_key:test_secret")
        result = await service.generate_token_request(
            user_id="user123",
            user_type="web",
            ttl=7200000  # 2 hours
        )

        # Current time (1640000000000) + TTL (7200000) = 1640007200000
        assert result.expires_at == 1640007200000

    @patch("ably.AblyRest")
    @patch("time.time")
    async def test_generate_token_request_with_custom_ttl(
        self, mock_time, mock_ably_rest
    ):
        """Test token generation with custom TTL."""
        mock_time.return_value = 1640000000.0
        mock_client = Mock()
        mock_auth = Mock()
        mock_ably_rest.return_value = mock_client
        mock_client.auth = mock_auth

        mock_token_request_obj = Mock()
        mock_token_request_obj.key_name = "test_key"
        mock_token_request_obj.client_id = "test_client"
        mock_token_request_obj.ttl = 1800000
        mock_token_request_obj.timestamp = 1640000000000
        mock_token_request_obj.capability = '{}'
        mock_token_request_obj.nonce = "test_nonce"
        mock_token_request_obj.mac = "test_mac"
        mock_auth.create_token_request = AsyncMock(return_value=mock_token_request_obj)

        service = AblyTokenService(api_key="test_key:test_secret")
        await service.generate_token_request(
            user_id="user123",
            user_type="web",
            ttl=1800000  # 30 minutes
        )

        call_args = mock_auth.create_token_request.call_args[0][0]
        assert call_args["ttl"] == 1800000
