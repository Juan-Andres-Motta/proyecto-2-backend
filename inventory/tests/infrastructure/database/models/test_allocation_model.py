"""Tests for the Allocation database model."""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from src.infrastructure.database.models.allocation import Allocation


class TestAllocationModel:
    """Test suite for Allocation model."""

    def test_allocation_creation_with_all_fields(self):
        """Test creating allocation with all required fields."""
        # Given
        order_id = uuid4()
        inventory_id = uuid4()
        allocation_id = uuid4()
        now = datetime.now(timezone.utc)

        # When
        allocation = Allocation(
            id=allocation_id,
            order_id=order_id,
            inventory_id=inventory_id,
            quantity=50,
            status="allocated",
            created_at=now,
            updated_at=now,
        )

        # Then
        assert allocation.id == allocation_id
        assert allocation.order_id == order_id
        assert allocation.inventory_id == inventory_id
        assert allocation.quantity == 50
        assert allocation.status == "allocated"
        assert allocation.created_at == now
        assert allocation.updated_at == now

    def test_allocation_with_explicit_status(self):
        """Test that allocation accepts explicit status value."""
        # Given
        order_id = uuid4()
        inventory_id = uuid4()

        # When
        allocation = Allocation(
            order_id=order_id,
            inventory_id=inventory_id,
            quantity=25,
            status="allocated",
        )

        # Then
        assert allocation.status == "allocated"

    def test_allocation_with_different_status(self):
        """Test allocation with different status values."""
        # Given
        order_id = uuid4()
        inventory_id = uuid4()

        # When
        for status in ["allocated", "released", "pending"]:
            allocation = Allocation(
                order_id=order_id,
                inventory_id=inventory_id,
                quantity=10,
                status=status,
            )

            # Then
            assert allocation.status == status

    def test_allocation_quantity_types(self):
        """Test allocation with different quantity values."""
        # Given
        order_id = uuid4()
        inventory_id = uuid4()

        # When/Then - Various quantities
        for quantity in [1, 10, 100, 1000]:
            allocation = Allocation(
                order_id=order_id,
                inventory_id=inventory_id,
                quantity=quantity,
            )
            assert allocation.quantity == quantity

    def test_allocation_multiple_items_for_same_order(self):
        """Test multiple allocations for the same order."""
        # Given
        order_id = uuid4()
        inv1_id = uuid4()
        inv2_id = uuid4()
        inv3_id = uuid4()

        # When - Create multiple allocations for same order
        allocations = [
            Allocation(order_id=order_id, inventory_id=inv1_id, quantity=50),
            Allocation(order_id=order_id, inventory_id=inv2_id, quantity=30),
            Allocation(order_id=order_id, inventory_id=inv3_id, quantity=20),
        ]

        # Then
        assert len(allocations) == 3
        assert all(a.order_id == order_id for a in allocations)
        assert allocations[0].quantity == 50
        assert allocations[1].quantity == 30
        assert allocations[2].quantity == 20

    def test_allocation_table_name(self):
        """Test that allocation uses correct table name."""
        # Then
        assert Allocation.__tablename__ == "allocations"

    def test_allocation_has_indexes(self):
        """Test that allocation model defines indexes."""
        # Then
        assert hasattr(Allocation, "__table_args__")
        table_args = Allocation.__table_args__
        # Should contain Index definitions
        assert len(table_args) > 0

    def test_allocation_with_different_order_and_inventory_ids(self):
        """Test allocations with various order and inventory combinations."""
        # Given
        order_ids = [uuid4() for _ in range(3)]
        inventory_ids = [uuid4() for _ in range(3)]

        # When - Create allocations for each order-inventory combination
        allocations = []
        for i, order_id in enumerate(order_ids):
            for j, inventory_id in enumerate(inventory_ids):
                allocation = Allocation(
                    order_id=order_id,
                    inventory_id=inventory_id,
                    quantity=(i + 1) * (j + 1) * 10,
                )
                allocations.append(allocation)

        # Then
        assert len(allocations) == 9  # 3x3 combinations
        # Verify each allocation has correct IDs
        for i, order_id in enumerate(order_ids):
            for j, inventory_id in enumerate(inventory_ids):
                idx = i * 3 + j
                assert allocations[idx].order_id == order_id
                assert allocations[idx].inventory_id == inventory_id

    def test_allocation_with_zero_quantity(self):
        """Test allocation with zero quantity (edge case)."""
        # Given
        order_id = uuid4()
        inventory_id = uuid4()

        # When
        allocation = Allocation(
            order_id=order_id,
            inventory_id=inventory_id,
            quantity=0,
        )

        # Then
        assert allocation.quantity == 0

    def test_allocation_with_large_quantity(self):
        """Test allocation with very large quantity."""
        # Given
        order_id = uuid4()
        inventory_id = uuid4()
        large_qty = 9_999_999

        # When
        allocation = Allocation(
            order_id=order_id,
            inventory_id=inventory_id,
            quantity=large_qty,
        )

        # Then
        assert allocation.quantity == large_qty

    def test_allocation_field_mapping(self):
        """Test that all Allocation fields are properly mapped."""
        # Given
        allocation_data = {
            "order_id": uuid4(),
            "inventory_id": uuid4(),
            "quantity": 75,
            "status": "released",
        }

        # When
        allocation = Allocation(**allocation_data)

        # Then
        assert allocation.order_id == allocation_data["order_id"]
        assert allocation.inventory_id == allocation_data["inventory_id"]
        assert allocation.quantity == allocation_data["quantity"]
        assert allocation.status == allocation_data["status"]
