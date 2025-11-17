"""
Unit tests for the authentication ports (abstract interfaces).

Tests that port interfaces are correctly defined and can be implemented.
"""

import pytest
from abc import ABC

from common.auth.ports import ClientPort


class TestClientPort:
    """Tests for the ClientPort interface."""

    def test_client_port_is_abstract_base_class(self):
        """Test that ClientPort is an abstract base class."""
        assert issubclass(ClientPort, ABC)

    def test_client_port_cannot_be_instantiated(self):
        """Test that ClientPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ClientPort()

    def test_client_port_can_be_subclassed(self):
        """Test that ClientPort can be subclassed."""
        class ConcreteClientPort(ClientPort):
            async def create_client(self, client_data):
                return {"id": "123", "email": "test@example.com"}

        # Should be able to instantiate subclass
        adapter = ConcreteClientPort()
        assert isinstance(adapter, ClientPort)

    def test_client_port_requires_create_client_implementation(self):
        """Test that create_client method must be implemented."""
        # Try to create a subclass without implementing create_client
        with pytest.raises(TypeError):
            class IncompletePort(ClientPort):
                pass

            IncompletePort()

    @pytest.mark.asyncio
    async def test_client_port_create_client_can_be_implemented(self):
        """Test that create_client can be implemented in subclass."""
        class TestClientPort(ClientPort):
            async def create_client(self, client_data):
                return client_data

        adapter = TestClientPort()
        result = await adapter.create_client({"email": "test@example.com", "name": "Test"})
        assert result == {"email": "test@example.com", "name": "Test"}
