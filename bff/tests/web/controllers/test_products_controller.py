"""
Unit tests for products controller.

Tests that controllers call the right ports.
"""

from unittest.mock import AsyncMock, Mock
from uuid import UUID
from decimal import Decimal

import pytest

from web.ports.catalog_port import CatalogPort
from web.controllers.products_controller import (
    get_products,
    create_product,
    create_products_from_csv,
)
from web.schemas.catalog_schemas import ProductCategory, ProductCreate


@pytest.fixture
def mock_catalog_port():
    """Create a mock catalog port."""
    return Mock(spec=CatalogPort)


class TestProductsControllerGetProducts:
    """Test get_products controller."""

    @pytest.mark.asyncio
    async def test_calls_port_and_returns_response(self, mock_catalog_port):
        """Test that get_products calls port and returns response."""
        expected_response = {
            "items": [],
            "total": 0,
            "page": 1,
            "size": 10,
            "has_next": False,
            "has_previous": False,
        }
        mock_catalog_port.get_products = AsyncMock(return_value=expected_response)

        result = await get_products(catalog=mock_catalog_port)

        mock_catalog_port.get_products.assert_called_once()
        assert result == expected_response


class TestProductsControllerCreateProduct:
    """Test create_product controller."""

    @pytest.mark.asyncio
    async def test_calls_port_and_returns_response(self, mock_catalog_port):
        """Test that create_product calls port with product data."""
        product_data = ProductCreate(
            provider_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            name="Test Product",
            category=ProductCategory.SPECIAL_MEDICATIONS,
            sku="PROD-001",
            price=Decimal("99.99"),
        )
        expected_response = {"created": [product_data], "count": 1}
        mock_catalog_port.create_products = AsyncMock(return_value=expected_response)

        result = await create_product(product=product_data, catalog=mock_catalog_port)

        mock_catalog_port.create_products.assert_called_once_with([product_data])
        assert result == expected_response


class TestProductsControllerCreateProductsFromCsv:
    """Test create_products_from_csv controller."""

    @pytest.mark.asyncio
    async def test_calls_port_and_returns_response(self, mock_catalog_port):
        """Test that create_products_from_csv parses CSV and calls port."""
        from fastapi import UploadFile
        import io

        csv_content = """provider_id,name,category,sku,price
550e8400-e29b-41d4-a716-446655440000,Product 1,medicamentos_especiales,PROD-001,99.99"""
        csv_bytes = csv_content.encode("utf-8")
        upload_file = UploadFile(filename="products.csv", file=io.BytesIO(csv_bytes))

        expected_response = {"created": [], "count": 1}
        mock_catalog_port.create_products = AsyncMock(return_value=expected_response)

        result = await create_products_from_csv(file=upload_file, catalog=mock_catalog_port)

        mock_catalog_port.create_products.assert_called_once()
        assert result == expected_response
