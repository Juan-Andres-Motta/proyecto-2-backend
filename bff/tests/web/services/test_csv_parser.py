"""
Unit tests for CsvParserService.

These tests focus on OUR CSV parsing logic:
- Parsing valid CSV files
- Validating data
- Handling errors (encoding, malformed data, validation)
"""

import io
from decimal import Decimal
from uuid import UUID

import pytest
from fastapi import UploadFile

from common.exceptions import ValidationError
from web.schemas.catalog_schemas import ProductCategory
from web.services.csv_parser import CsvParserService


class TestCsvParserServiceValidCases:
    """Test CSV parser with valid input."""

    @pytest.mark.asyncio
    async def test_parses_single_product(self):
        """Test parsing a CSV file with a single valid product."""
        csv_content = """provider_id,name,category,sku,price
550e8400-e29b-41d4-a716-446655440000,Aspirin 500mg,medicamentos_especiales,MED-001,15.99"""

        csv_bytes = csv_content.encode("utf-8")
        upload_file = UploadFile(filename="products.csv", file=io.BytesIO(csv_bytes))

        products = await CsvParserService.parse_products_from_csv(upload_file)

        assert len(products) == 1
        assert products[0].name == "Aspirin 500mg"
        assert products[0].provider_id == UUID("550e8400-e29b-41d4-a716-446655440000")
        assert products[0].category == ProductCategory.SPECIAL_MEDICATIONS
        assert products[0].sku == "MED-001"
        assert products[0].price == Decimal("15.99")

    @pytest.mark.asyncio
    async def test_parses_multiple_products(self):
        """Test parsing a CSV file with multiple products."""
        csv_content = """provider_id,name,category,sku,price
550e8400-e29b-41d4-a716-446655440000,Product 1,medicamentos_especiales,PROD-001,100.00
550e8400-e29b-41d4-a716-446655440000,Product 2,insumos_quirurgicos,PROD-002,200.50
550e8400-e29b-41d4-a716-446655440000,Product 3,reactivos_diagnosticos,PROD-003,75.25"""

        csv_bytes = csv_content.encode("utf-8")
        upload_file = UploadFile(filename="products.csv", file=io.BytesIO(csv_bytes))

        products = await CsvParserService.parse_products_from_csv(upload_file)

        assert len(products) == 3
        assert products[0].name == "Product 1"
        assert products[0].category == ProductCategory.SPECIAL_MEDICATIONS
        assert products[1].name == "Product 2"
        assert products[1].category == ProductCategory.SURGICAL_SUPPLIES
        assert products[2].name == "Product 3"
        assert products[2].category == ProductCategory.DIAGNOSTIC_REAGENTS

    @pytest.mark.asyncio
    async def test_handles_whitespace_in_values(self):
        """Test that whitespace in CSV values is trimmed."""
        csv_content = """provider_id,name,category,sku,price
 550e8400-e29b-41d4-a716-446655440000 , Product Name , medicamentos_especiales , SKU-001 , 99.99 """

        csv_bytes = csv_content.encode("utf-8")
        upload_file = UploadFile(filename="products.csv", file=io.BytesIO(csv_bytes))

        products = await CsvParserService.parse_products_from_csv(upload_file)

        assert len(products) == 1
        assert products[0].name == "Product Name"
        assert products[0].sku == "SKU-001"
        assert products[0].price == Decimal("99.99")

    @pytest.mark.asyncio
    async def test_parses_all_product_categories(self):
        """Test that all valid product categories are accepted."""
        csv_content = """provider_id,name,category,sku,price
550e8400-e29b-41d4-a716-446655440000,Med,medicamentos_especiales,SKU-1,10.00
550e8400-e29b-41d4-a716-446655440000,Ins,insumos_quirurgicos,SKU-2,20.00
550e8400-e29b-41d4-a716-446655440000,Rea,reactivos_diagnosticos,SKU-3,30.00
550e8400-e29b-41d4-a716-446655440000,Equ,equipos_biomedicos,SKU-4,40.00
550e8400-e29b-41d4-a716-446655440000,Otr,otros,SKU-5,50.00"""

        csv_bytes = csv_content.encode("utf-8")
        upload_file = UploadFile(filename="products.csv", file=io.BytesIO(csv_bytes))

        products = await CsvParserService.parse_products_from_csv(upload_file)

        assert len(products) == 5
        assert products[0].category == ProductCategory.SPECIAL_MEDICATIONS
        assert products[1].category == ProductCategory.SURGICAL_SUPPLIES
        assert products[2].category == ProductCategory.DIAGNOSTIC_REAGENTS
        assert products[3].category == ProductCategory.BIOMEDICAL_EQUIPMENT
        assert products[4].category == ProductCategory.OTHER


class TestCsvParserServiceFileValidation:
    """Test CSV parser file validation logic."""

    @pytest.mark.asyncio
    async def test_rejects_non_csv_file(self):
        """Test that non-CSV files are rejected."""
        upload_file = UploadFile(filename="products.txt", file=io.BytesIO(b"data"))

        with pytest.raises(ValidationError) as exc_info:
            await CsvParserService.parse_products_from_csv(upload_file)

        assert "File must be a CSV file" in str(exc_info.value.message)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_rejects_empty_csv(self):
        """Test that empty CSV files are rejected."""
        csv_content = """provider_id,name,category,sku,price"""  # Header only

        csv_bytes = csv_content.encode("utf-8")
        upload_file = UploadFile(filename="products.csv", file=io.BytesIO(csv_bytes))

        with pytest.raises(ValidationError) as exc_info:
            await CsvParserService.parse_products_from_csv(upload_file)

        assert "empty" in str(exc_info.value.message).lower()


class TestCsvParserServiceEncodingErrors:
    """Test CSV parser encoding error handling."""

    @pytest.mark.asyncio
    async def test_rejects_invalid_encoding(self):
        """Test that invalid UTF-8 encoding is rejected."""
        # Create invalid UTF-8 bytes
        invalid_bytes = b"\xff\xfe\xfd"

        upload_file = UploadFile(filename="products.csv", file=io.BytesIO(invalid_bytes))

        with pytest.raises(ValidationError) as exc_info:
            await CsvParserService.parse_products_from_csv(upload_file)

        assert "UTF-8" in str(exc_info.value.message)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_handles_utf8_bom(self):
        """Test that UTF-8 BOM is handled correctly."""
        csv_content = """provider_id,name,category,sku,price
550e8400-e29b-41d4-a716-446655440000,Product,medicamentos_especiales,SKU-001,10.00"""

        # Add UTF-8 BOM
        csv_bytes = b"\xef\xbb\xbf" + csv_content.encode("utf-8")
        upload_file = UploadFile(filename="products.csv", file=io.BytesIO(csv_bytes))

        products = await CsvParserService.parse_products_from_csv(upload_file)

        assert len(products) == 1
        assert products[0].name == "Product"


class TestCsvParserServiceMalformedCsv:
    """Test CSV parser with malformed CSV files."""

    @pytest.mark.asyncio
    async def test_handles_missing_columns(self):
        """Test that CSVs with missing columns fail validation."""
        csv_content = """provider_id,name,category,sku,price
550e8400-e29b-41d4-a716-446655440000,Product,medicamentos_especiales,10.00"""  # Missing SKU

        csv_bytes = csv_content.encode("utf-8")
        upload_file = UploadFile(filename="products.csv", file=io.BytesIO(csv_bytes))

        with pytest.raises(ValidationError) as exc_info:
            await CsvParserService.parse_products_from_csv(upload_file)

        assert "CSV row 2" in str(exc_info.value.message)
