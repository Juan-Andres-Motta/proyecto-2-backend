"""Unit tests for RealtimePublisher."""

import pytest
from unittest.mock import Mock, patch

from common.realtime.publisher import RealtimePublisher, get_publisher, reset_publisher


class TestRealtimePublisherInit:
    """Tests for publisher initialization."""

    def test_init_stores_configuration(self):
        """Test constructor stores API key and environment."""
        publisher = RealtimePublisher(api_key="test.key:secret", environment="dev")

        assert publisher.api_key == "test.key:secret"
        assert publisher.environment == "dev"
        assert publisher._client is None

    def test_init_defaults_to_prod_environment(self):
        """Test default environment is prod."""
        publisher = RealtimePublisher(api_key="test.key:secret")

        assert publisher.environment == "prod"

    def test_init_with_empty_api_key_logs_warning(self, caplog):
        """Test warning logged when API key is empty."""
        publisher = RealtimePublisher(api_key="")

        assert "Ably API key not provided" in caplog.text


class TestRealtimePublisherGetClient:
    """Tests for _get_client() lazy loading."""

    @patch("ably.AblyRest")
    def test_get_client_creates_ably_rest_client(self, mock_ably_rest):
        """Test client is created with correct API key."""
        publisher = RealtimePublisher(api_key="test.key:secret")

        client = publisher._get_client()

        mock_ably_rest.assert_called_once_with("test.key:secret")
        assert client == mock_ably_rest.return_value

    @patch("ably.AblyRest")
    def test_get_client_caches_instance(self, mock_ably_rest):
        """Test client is only created once."""
        publisher = RealtimePublisher(api_key="test.key:secret")

        client1 = publisher._get_client()
        client2 = publisher._get_client()

        assert mock_ably_rest.call_count == 1
        assert client1 is client2

    def test_get_client_raises_import_error_if_ably_not_installed(self):
        """Test raises ImportError if ably package not installed."""
        publisher = RealtimePublisher(api_key="test.key:secret")

        with patch.dict("sys.modules", {"ably": None}):
            with pytest.raises(ImportError):
                publisher._get_client()


class TestRealtimePublisherPublish:
    """Tests for publish() method."""

    @patch("ably.AblyRest")
    def test_publish_sends_event_to_ably(self, mock_ably_rest):
        """Test publish sends event to correct channel."""
        mock_client = Mock()
        mock_channel = Mock()
        mock_ably_rest.return_value = mock_client
        mock_client.channels.get.return_value = mock_channel

        publisher = RealtimePublisher(api_key="test.key:secret", environment="dev")
        publisher.publish("sellers:inventory", "stock.updated")

        mock_client.channels.get.assert_called_once_with("dev:sellers:inventory")
        mock_channel.publish.assert_called_once_with("stock.updated", {})

    @patch("ably.AblyRest")
    def test_publish_with_data_sends_data(self, mock_ably_rest):
        """Test publish includes data payload."""
        mock_client = Mock()
        mock_channel = Mock()
        mock_ably_rest.return_value = mock_client
        mock_client.channels.get.return_value = mock_channel

        publisher = RealtimePublisher(api_key="test.key:secret", environment="prod")
        publisher.publish("users:123", "order.created", {"order_id": "456"})

        mock_channel.publish.assert_called_once_with("order.created", {"order_id": "456"})

    @patch("ably.AblyRest")
    def test_publish_auto_prefixes_channel_with_environment(self, mock_ably_rest):
        """Test channel is prefixed with environment."""
        mock_client = Mock()
        mock_channel = Mock()
        mock_ably_rest.return_value = mock_client
        mock_client.channels.get.return_value = mock_channel

        publisher = RealtimePublisher(api_key="test.key:secret", environment="staging")
        publisher.publish("test:channel", "event")

        mock_client.channels.get.assert_called_once_with("staging:test:channel")

    @patch("ably.AblyRest")
    def test_publish_does_not_double_prefix(self, mock_ably_rest):
        """Test channel already prefixed is not double-prefixed."""
        mock_client = Mock()
        mock_channel = Mock()
        mock_ably_rest.return_value = mock_client
        mock_client.channels.get.return_value = mock_channel

        publisher = RealtimePublisher(api_key="test.key:secret", environment="dev")
        publisher.publish("dev:already:prefixed", "event")

        mock_client.channels.get.assert_called_once_with("dev:already:prefixed")

    def test_publish_without_api_key_logs_warning(self, caplog):
        """Test publish logs warning when API key is empty."""
        publisher = RealtimePublisher(api_key="")

        publisher.publish("test", "event")

        assert "Ably not configured - skipping publish" in caplog.text

    @patch("ably.AblyRest")
    def test_publish_logs_error_on_failure(self, mock_ably_rest, caplog):
        """Test publish logs error but doesn't raise."""
        mock_client = Mock()
        mock_ably_rest.return_value = mock_client
        mock_client.channels.get.side_effect = Exception("Connection failed")

        publisher = RealtimePublisher(api_key="test.key:secret")

        publisher.publish("test", "event")

        assert "Failed to publish to Ably" in caplog.text


class TestRealtimePublisherPublishBatch:
    """Tests for publish_batch() method."""

    @patch("ably.AblyRest")
    def test_publish_batch_calls_publish_for_each_message(self, mock_ably_rest):
        """Test batch iterates and publishes each message."""
        mock_client = Mock()
        mock_channel = Mock()
        mock_ably_rest.return_value = mock_client
        mock_client.channels.get.return_value = mock_channel

        publisher = RealtimePublisher(api_key="test.key:secret", environment="dev")
        publisher.publish_batch([
            ("channel1", "event1", None),
            ("channel2", "event2", {"data": "test"}),
        ])

        assert mock_channel.publish.call_count == 2

    def test_publish_batch_without_api_key_logs_warning(self, caplog):
        """Test batch publish logs warning when API key is empty."""
        publisher = RealtimePublisher(api_key="")

        publisher.publish_batch([("test", "event", None)])

        assert "Ably not configured - skipping batch publish" in caplog.text


class TestRealtimePublisherHealthCheck:
    """Tests for health_check() method."""

    @patch("ably.AblyRest")
    def test_health_check_returns_true_when_ably_reachable(self, mock_ably_rest):
        """Test health check returns True when Ably responds."""
        mock_client = Mock()
        mock_ably_rest.return_value = mock_client
        mock_client.time.return_value = 1234567890

        publisher = RealtimePublisher(api_key="test.key:secret")

        assert publisher.health_check() is True

    @patch("ably.AblyRest")
    def test_health_check_returns_false_on_error(self, mock_ably_rest):
        """Test health check returns False when Ably fails."""
        mock_client = Mock()
        mock_ably_rest.return_value = mock_client
        mock_client.time.side_effect = Exception("Network error")

        publisher = RealtimePublisher(api_key="test.key:secret")

        assert publisher.health_check() is False

    def test_health_check_returns_false_without_api_key(self):
        """Test health check returns False when no API key."""
        publisher = RealtimePublisher(api_key="")

        assert publisher.health_check() is False


class TestGetPublisher:
    """Tests for get_publisher() factory function."""

    def setup_method(self):
        """Reset publisher before each test."""
        reset_publisher()

    @patch("config.settings.settings")
    def test_get_publisher_creates_singleton(self, mock_settings):
        """Test factory creates and caches singleton."""
        mock_settings.ably_api_key = "test.key:secret"
        mock_settings.ably_environment = "dev"

        publisher1 = get_publisher()
        publisher2 = get_publisher()

        assert publisher1 is publisher2

    @patch("config.settings.settings")
    def test_reset_publisher_clears_singleton(self, mock_settings):
        """Test reset clears cached instance."""
        mock_settings.ably_api_key = "test.key:secret"
        mock_settings.ably_environment = "dev"

        publisher1 = get_publisher()
        reset_publisher()
        publisher2 = get_publisher()

        assert publisher1 is not publisher2
