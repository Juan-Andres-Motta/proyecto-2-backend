"""Unit tests for providers controller."""

from unittest.mock import AsyncMock, Mock
from uuid import UUID
import pytest

from web.ports.catalog_port import CatalogPort
from web.controllers.providers_controller import create_provider, get_providers
from web.schemas.catalog_schemas import ProviderCreate


@pytest.fixture
def mock_catalog_port():
    return Mock(spec=CatalogPort)


class TestProvidersController:
    @pytest.mark.asyncio
    async def test_create_provider(self, mock_catalog_port):
        provider_data = ProviderCreate(
            name="Test", nit="123", contact_name="John", email="test@test.com",
            phone="123", address="addr", country="US"
        )
        mock_catalog_port.create_provider = AsyncMock(return_value={"id": "test-id"})

        result = await create_provider(provider=provider_data, catalog=mock_catalog_port)

        mock_catalog_port.create_provider.assert_called_once_with(provider_data)
        assert result == {"id": "test-id"}

    @pytest.mark.asyncio
    async def test_get_providers(self, mock_catalog_port):
        mock_catalog_port.get_providers = AsyncMock(return_value={"items": [], "total": 0})

        result = await get_providers(catalog=mock_catalog_port)

        mock_catalog_port.get_providers.assert_called_once()
        assert result == {"items": [], "total": 0}
