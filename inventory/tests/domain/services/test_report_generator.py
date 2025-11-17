"""Unit tests for LowStockReportGenerator."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.repositories.inventory_repository import (
    InventoryRepository,
)
from src.domain.services.report_generator import LowStockReportGenerator


@pytest.fixture
async def sample_inventory_data(db_session: AsyncSession):
    """Create sample inventory data for testing."""
    inventory_repo = InventoryRepository(db_session)
    warehouse_id_1 = uuid.uuid4()
    warehouse_id_2 = uuid.uuid4()

    inventories = []

    # Create low stock items (available < 10)
    for i in range(3):
        inventory_data = {
            "product_id": uuid.uuid4(),
            "warehouse_id": warehouse_id_1,
            "total_quantity": 8 - i,  # 8, 7, 6
            "reserved_quantity": 0,
            "batch_number": f"BATCH00{i}",
            "expiration_date": datetime(2026, 12, 31, tzinfo=timezone.utc),
            "product_sku": f"SKU-LOW-{i}",
            "product_name": f"Low Stock Product {i}",
            "product_price": Decimal("50.00"),
            "warehouse_name": "Warehouse A",
            "warehouse_city": "City A",
        "warehouse_country": "Colombia",
        }
        inv = await inventory_repo.create(inventory_data)
        inventories.append(inv)

    # Create normal stock items (available >= 10)
    for i in range(2):
        inventory_data = {
            "product_id": uuid.uuid4(),
            "warehouse_id": warehouse_id_2,
            "total_quantity": 50 + i,
            "reserved_quantity": 10,
            "batch_number": f"BATCH10{i}",
            "expiration_date": datetime(2026, 12, 31, tzinfo=timezone.utc),
            "product_sku": f"SKU-NORMAL-{i}",
            "product_name": f"Normal Stock Product {i}",
            "product_price": Decimal("100.00"),
            "warehouse_name": "Warehouse B",
            "warehouse_city": "City B",
        "warehouse_country": "Colombia",
        }
        inv = await inventory_repo.create(inventory_data)
        inventories.append(inv)

    # Create critical stock item (available = 0)
    critical_data = {
        "product_id": uuid.uuid4(),
        "warehouse_id": warehouse_id_1,
        "total_quantity": 5,
        "reserved_quantity": 5,  # All reserved, 0 available
        "batch_number": "BATCH-CRITICAL",
        "expiration_date": datetime(2026, 12, 31, tzinfo=timezone.utc),
        "product_sku": "SKU-CRITICAL",
        "product_name": "Critical Stock Product",
        "product_price": Decimal("75.00"),
        "warehouse_name": "Warehouse A",
        "warehouse_city": "City A",
        "warehouse_country": "Colombia",
    }
    critical = await inventory_repo.create(critical_data)
    inventories.append(critical)

    return {
        "inventories": inventories,
        "warehouse_id_1": warehouse_id_1,
        "warehouse_id_2": warehouse_id_2,
    }


@pytest.mark.asyncio
async def test_generate_low_stock_report_default_threshold(
    db_session: AsyncSession, sample_inventory_data
):
    """Test generating low stock report with default threshold (10)."""
    generator = LowStockReportGenerator(db_session)

    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

    report = await generator.generate(start_date, end_date)

    # Should include 4 items: 3 low stock (8,7,6 available) + 1 critical (0 available)
    assert report["report_type"] == "low_stock"
    assert len(report["data"]) == 4
    assert report["summary"]["total_low_stock_items"] == 4
    assert report["summary"]["critical_items"] == 1
    assert report["filters"]["threshold"] == 10

    # Verify data is sorted by available quantity ascending
    available_quantities = [item["available_quantity"] for item in report["data"]]
    assert available_quantities == sorted(available_quantities)


@pytest.mark.asyncio
async def test_generate_low_stock_report_custom_threshold(
    db_session: AsyncSession, sample_inventory_data
):
    """Test generating low stock report with custom threshold."""
    generator = LowStockReportGenerator(db_session)

    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)
    filters = {"threshold": 7}

    report = await generator.generate(start_date, end_date, filters)

    # Should include 2 items: 1 low stock (6 available) + 1 critical (0 available)
    assert len(report["data"]) == 2
    assert report["summary"]["total_low_stock_items"] == 2
    assert report["filters"]["threshold"] == 7


@pytest.mark.asyncio
async def test_generate_low_stock_report_warehouse_filter(
    db_session: AsyncSession, sample_inventory_data
):
    """Test filtering low stock report by warehouse."""
    generator = LowStockReportGenerator(db_session)

    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)
    filters = {"warehouse_id": str(sample_inventory_data["warehouse_id_1"])}

    report = await generator.generate(start_date, end_date, filters)

    # Should only include items from warehouse 1 (3 low stock + 1 critical)
    assert len(report["data"]) == 4
    assert all(
        item["warehouse_id"] == str(sample_inventory_data["warehouse_id_1"])
        for item in report["data"]
    )
    assert report["filters"]["warehouse_id"] == str(
        sample_inventory_data["warehouse_id_1"]
    )


@pytest.mark.asyncio
async def test_generate_low_stock_report_no_low_stock_items(db_session: AsyncSession):
    """Test generating report when no low stock items exist."""
    inventory_repo = InventoryRepository(db_session)

    # Create only normal stock items
    for i in range(2):
        inventory_data = {
            "product_id": uuid.uuid4(),
            "warehouse_id": uuid.uuid4(),
            "total_quantity": 100,
            "reserved_quantity": 10,
            "batch_number": f"BATCH{i}",
            "expiration_date": datetime(2026, 12, 31, tzinfo=timezone.utc),
            "product_sku": f"SKU-{i}",
            "product_name": f"Product {i}",
            "product_price": Decimal("100.00"),
            "warehouse_name": "Warehouse",
            "warehouse_city": "City",
        "warehouse_country": "Colombia",
        }
        await inventory_repo.create(inventory_data)

    generator = LowStockReportGenerator(db_session)
    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

    report = await generator.generate(start_date, end_date)

    assert len(report["data"]) == 0
    assert report["summary"]["total_low_stock_items"] == 0
    assert report["summary"]["critical_items"] == 0
    assert report["summary"]["affected_warehouses"] == 0


@pytest.mark.asyncio
async def test_generate_low_stock_report_data_format(
    db_session: AsyncSession, sample_inventory_data
):
    """Test that report data has correct format and fields."""
    generator = LowStockReportGenerator(db_session)

    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

    report = await generator.generate(start_date, end_date)

    # Verify report structure
    assert "report_type" in report
    assert "generated_at" in report
    assert "date_range" in report
    assert "filters" in report
    assert "data" in report
    assert "summary" in report

    # Verify data item structure
    if len(report["data"]) > 0:
        item = report["data"][0]
        required_fields = [
            "inventory_id",
            "product_id",
            "product_sku",
            "product_name",
            "warehouse_id",
            "warehouse_name",
            "warehouse_city",
            "total_quantity",
            "reserved_quantity",
            "available_quantity",
            "batch_number",
            "expiration_date",
            "product_price",
        ]
        for field in required_fields:
            assert field in item

    # Verify summary structure
    summary_fields = [
        "total_low_stock_items",
        "total_available_quantity",
        "critical_items",
        "affected_warehouses",
        "warehouses",
    ]
    for field in summary_fields:
        assert field in report["summary"]


@pytest.mark.asyncio
async def test_generate_low_stock_report_available_quantity_calculation(
    db_session: AsyncSession
):
    """Test that available quantity is calculated correctly."""
    inventory_repo = InventoryRepository(db_session)

    inventory_data = {
        "product_id": uuid.uuid4(),
        "warehouse_id": uuid.uuid4(),
        "total_quantity": 25,
        "reserved_quantity": 20,
        "batch_number": "BATCH001",
        "expiration_date": datetime(2026, 12, 31, tzinfo=timezone.utc),
        "product_sku": "SKU-TEST",
        "product_name": "Test Product",
        "product_price": Decimal("50.00"),
        "warehouse_name": "Test Warehouse",
        "warehouse_city": "Test City",
        "warehouse_country": "Colombia",
    }
    await inventory_repo.create(inventory_data)

    generator = LowStockReportGenerator(db_session)
    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

    report = await generator.generate(start_date, end_date)

    # Available = 25 - 20 = 5 (below default threshold of 10)
    assert len(report["data"]) == 1
    assert report["data"][0]["total_quantity"] == 25
    assert report["data"][0]["reserved_quantity"] == 20
    assert report["data"][0]["available_quantity"] == 5


@pytest.mark.asyncio
async def test_generate_low_stock_report_warehouse_grouping(
    db_session: AsyncSession, sample_inventory_data
):
    """Test that summary includes warehouse grouping."""
    generator = LowStockReportGenerator(db_session)

    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

    report = await generator.generate(start_date, end_date)

    # Should have warehouses summary
    assert "warehouses" in report["summary"]
    assert len(report["summary"]["warehouses"]) > 0

    # Each warehouse should have required fields
    for warehouse in report["summary"]["warehouses"]:
        assert "warehouse_id" in warehouse
        assert "warehouse_name" in warehouse
        assert "warehouse_city" in warehouse
        assert "low_stock_items" in warehouse


@pytest.mark.asyncio
async def test_generate_low_stock_report_invalid_warehouse_id(
    db_session: AsyncSession, sample_inventory_data
):
    """Test that invalid warehouse_id is handled gracefully."""
    generator = LowStockReportGenerator(db_session)

    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)
    filters = {"warehouse_id": "invalid-uuid-format"}

    # Should not raise exception, just skip the invalid filter
    report = await generator.generate(start_date, end_date, filters)

    # Should return all low stock items (filter ignored due to invalid format)
    assert len(report["data"]) == 4
    assert report["filters"]["warehouse_id"] == "invalid-uuid-format"


@pytest.mark.asyncio
async def test_generate_low_stock_report_total_available_quantity(
    db_session: AsyncSession, sample_inventory_data
):
    """Test that total_available_quantity is calculated correctly."""
    generator = LowStockReportGenerator(db_session)

    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

    report = await generator.generate(start_date, end_date)

    # Calculate expected total: 8 + 7 + 6 + 0 = 21
    expected_total = sum(item["available_quantity"] for item in report["data"])
    assert report["summary"]["total_available_quantity"] == expected_total
    assert report["summary"]["total_available_quantity"] == 21
