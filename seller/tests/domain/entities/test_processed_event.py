"""Unit tests for ProcessedEvent domain entity."""

import json
from datetime import datetime
from uuid import UUID, uuid4

import pytest

from src.domain.entities.processed_event import ProcessedEvent


class TestProcessedEventInit:
    """Tests for ProcessedEvent initialization."""

    def test_init_with_all_parameters(self):
        """Test initializing ProcessedEvent with all parameters."""
        event_id = str(uuid4())
        id_uuid = uuid4()
        now = datetime.utcnow()
        payload = '{"order_id": "123"}'

        event = ProcessedEvent(
            id=id_uuid,
            event_id=event_id,
            event_type="order_created",
            processed_at=now,
            microservice="order",
            payload_snapshot=payload,
        )

        assert event.id == id_uuid
        assert event.event_id == event_id
        assert event.event_type == "order_created"
        assert event.processed_at == now
        assert event.microservice == "order"
        assert event.payload_snapshot == payload

    def test_init_event_id_is_string(self):
        """Test that event_id is stored as string."""
        event_id = str(uuid4())
        event = ProcessedEvent(
            id=uuid4(),
            event_id=event_id,
            event_type="order_created",
            processed_at=datetime.utcnow(),
            microservice="order",
            payload_snapshot="{}",
        )

        assert isinstance(event.event_id, str)
        assert event.event_id == event_id

    def test_init_id_is_uuid(self):
        """Test that id is stored as UUID."""
        id_uuid = uuid4()
        event = ProcessedEvent(
            id=id_uuid,
            event_id=str(uuid4()),
            event_type="order_created",
            processed_at=datetime.utcnow(),
            microservice="order",
            payload_snapshot="{}",
        )

        assert isinstance(event.id, UUID)
        assert event.id == id_uuid

    def test_init_processed_at_is_datetime(self):
        """Test that processed_at is stored as datetime."""
        now = datetime.utcnow()
        event = ProcessedEvent(
            id=uuid4(),
            event_id=str(uuid4()),
            event_type="order_created",
            processed_at=now,
            microservice="order",
            payload_snapshot="{}",
        )

        assert isinstance(event.processed_at, datetime)
        assert event.processed_at == now


class TestCreateNew:
    """Tests for ProcessedEvent.create_new factory method."""

    def test_create_new_generates_uuid(self):
        """Test that create_new generates a new UUID for id."""
        event = ProcessedEvent.create_new(
            event_id="evt-123",
            event_type="order_created",
            microservice="order",
            payload_snapshot='{"order_id": "123"}',
        )

        assert isinstance(event.id, UUID)
        assert event.id is not None

    def test_create_new_sets_event_id(self):
        """Test that create_new sets the provided event_id."""
        event_id = "evt-12345"
        event = ProcessedEvent.create_new(
            event_id=event_id,
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )

        assert event.event_id == event_id

    def test_create_new_sets_event_type(self):
        """Test that create_new sets the provided event_type."""
        event = ProcessedEvent.create_new(
            event_id="evt-123",
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )

        assert event.event_type == "order_created"

    def test_create_new_sets_microservice(self):
        """Test that create_new sets the provided microservice."""
        event = ProcessedEvent.create_new(
            event_id="evt-123",
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )

        assert event.microservice == "order"

    def test_create_new_sets_payload_snapshot(self):
        """Test that create_new sets the provided payload_snapshot."""
        payload = '{"order_id": "123", "customer_id": "456"}'
        event = ProcessedEvent.create_new(
            event_id="evt-123",
            event_type="order_created",
            microservice="order",
            payload_snapshot=payload,
        )

        assert event.payload_snapshot == payload

    def test_create_new_sets_processed_at_to_current_time(self):
        """Test that create_new sets processed_at to current UTC time."""
        before_create = datetime.utcnow()
        event = ProcessedEvent.create_new(
            event_id="evt-123",
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )
        after_create = datetime.utcnow()

        # processed_at should be set and be within the time range
        assert before_create <= event.processed_at <= after_create

    def test_create_new_with_seller_event(self):
        """Test create_new with seller microservice event."""
        event = ProcessedEvent.create_new(
            event_id="evt-seller-456",
            event_type="order_created",
            microservice="seller",
            payload_snapshot='{"seller_id": "789"}',
        )

        assert event.event_type == "order_created"
        assert event.microservice == "seller"
        assert "seller_id" in event.payload_snapshot

    def test_create_new_with_complex_payload(self):
        """Test create_new with complex JSON payload."""
        complex_payload = json.dumps({
            "order_id": "123",
            "customer_id": "456",
            "items": [
                {"product_id": "p1", "quantity": 5},
                {"product_id": "p2", "quantity": 3},
            ],
            "total": 1250.50,
        })

        event = ProcessedEvent.create_new(
            event_id="evt-complex",
            event_type="order_created",
            microservice="order",
            payload_snapshot=complex_payload,
        )

        # Verify we can parse the payload back
        parsed = json.loads(event.payload_snapshot)
        assert parsed["order_id"] == "123"
        assert len(parsed["items"]) == 2


class TestRepr:
    """Tests for ProcessedEvent string representation."""

    def test_repr_includes_event_id(self):
        """Test that repr includes event_id."""
        event = ProcessedEvent.create_new(
            event_id="evt-test-123",
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )

        repr_str = repr(event)
        assert "evt-test-123" in repr_str

    def test_repr_includes_event_type(self):
        """Test that repr includes event_type."""
        event = ProcessedEvent.create_new(
            event_id="evt-123",
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )

        repr_str = repr(event)
        assert "order_created" in repr_str

    def test_repr_includes_microservice(self):
        """Test that repr includes microservice."""
        event = ProcessedEvent.create_new(
            event_id="evt-123",
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )

        repr_str = repr(event)
        assert "order" in repr_str

    def test_repr_format(self):
        """Test the format of repr string."""
        event = ProcessedEvent.create_new(
            event_id="evt-abc",
            event_type="order_created",
            microservice="seller",
            payload_snapshot="{}",
        )

        repr_str = repr(event)

        # Should follow format: ProcessedEvent(event_id=..., event_type=..., microservice=...)
        assert "ProcessedEvent(" in repr_str
        assert "event_id=evt-abc" in repr_str
        assert "event_type=order_created" in repr_str
        assert "microservice=seller" in repr_str

    def test_repr_is_useful_for_logging(self):
        """Test that repr is useful for logging purposes."""
        event = ProcessedEvent.create_new(
            event_id="evt-log-test",
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )

        repr_str = repr(event)

        # Should be concise and contain key info
        assert len(repr_str) < 200
        assert all(key in repr_str for key in ["event_id", "event_type", "microservice"])


class TestDataclass:
    """Tests for ProcessedEvent dataclass behavior."""

    def test_is_dataclass(self):
        """Test that ProcessedEvent is a dataclass."""
        event = ProcessedEvent.create_new(
            event_id="evt-123",
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )

        # Should have expected attributes
        assert hasattr(event, "id")
        assert hasattr(event, "event_id")
        assert hasattr(event, "event_type")
        assert hasattr(event, "processed_at")
        assert hasattr(event, "microservice")
        assert hasattr(event, "payload_snapshot")

    def test_equality(self):
        """Test dataclass equality."""
        id1 = uuid4()
        now = datetime.utcnow()

        event1 = ProcessedEvent(
            id=id1,
            event_id="evt-123",
            event_type="order_created",
            processed_at=now,
            microservice="order",
            payload_snapshot="{}",
        )

        event2 = ProcessedEvent(
            id=id1,
            event_id="evt-123",
            event_type="order_created",
            processed_at=now,
            microservice="order",
            payload_snapshot="{}",
        )

        assert event1 == event2

    def test_inequality(self):
        """Test dataclass inequality."""
        now = datetime.utcnow()

        event1 = ProcessedEvent(
            id=uuid4(),
            event_id="evt-123",
            event_type="order_created",
            processed_at=now,
            microservice="order",
            payload_snapshot="{}",
        )

        event2 = ProcessedEvent(
            id=uuid4(),
            event_id="evt-456",
            event_type="order_created",
            processed_at=now,
            microservice="order",
            payload_snapshot="{}",
        )

        assert event1 != event2


class TestIdempotencyTracking:
    """Tests for idempotency tracking functionality."""

    def test_event_id_unique_identifier(self):
        """Test that event_id serves as unique identifier for events."""
        event_id_1 = "evt-order-001"
        event_id_2 = "evt-order-002"

        event1 = ProcessedEvent.create_new(
            event_id=event_id_1,
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )

        event2 = ProcessedEvent.create_new(
            event_id=event_id_2,
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )

        # event_id should be unique
        assert event1.event_id != event2.event_id

    def test_payload_snapshot_preserves_event_data(self):
        """Test that payload_snapshot preserves original event data."""
        payload = {
            "order_id": "order-123",
            "customer_id": "cust-456",
            "total": 1250.50,
        }
        payload_json = json.dumps(payload)

        event = ProcessedEvent.create_new(
            event_id="evt-123",
            event_type="order_created",
            microservice="order",
            payload_snapshot=payload_json,
        )

        # Should be able to reconstruct original data
        reconstructed = json.loads(event.payload_snapshot)
        assert reconstructed["order_id"] == "order-123"
        assert reconstructed["customer_id"] == "cust-456"
        assert reconstructed["total"] == 1250.50

    def test_microservice_identification(self):
        """Test that microservice field identifies event source."""
        order_event = ProcessedEvent.create_new(
            event_id="evt-1",
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )

        seller_event = ProcessedEvent.create_new(
            event_id="evt-2",
            event_type="order_created",
            microservice="seller",
            payload_snapshot="{}",
        )

        assert order_event.microservice == "order"
        assert seller_event.microservice == "seller"


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_create_new_with_empty_payload(self):
        """Test create_new with empty JSON payload."""
        event = ProcessedEvent.create_new(
            event_id="evt-123",
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )

        assert event.payload_snapshot == "{}"

    def test_create_new_with_large_payload(self):
        """Test create_new with large JSON payload."""
        large_payload = json.dumps({
            "items": [{"id": f"item-{i}", "value": i} for i in range(100)]
        })

        event = ProcessedEvent.create_new(
            event_id="evt-123",
            event_type="order_created",
            microservice="order",
            payload_snapshot=large_payload,
        )

        # Should handle large payloads
        assert len(event.payload_snapshot) > 1000
        parsed = json.loads(event.payload_snapshot)
        assert len(parsed["items"]) == 100

    def test_create_new_with_special_characters_in_event_id(self):
        """Test create_new with special characters in event_id."""
        event_id = "evt-2025-11-09T12:34:56Z-123"

        event = ProcessedEvent.create_new(
            event_id=event_id,
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )

        assert event.event_id == event_id

    def test_create_new_generates_unique_ids(self):
        """Test that multiple create_new calls generate unique UUIDs."""
        event1 = ProcessedEvent.create_new(
            event_id="evt-1",
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )

        event2 = ProcessedEvent.create_new(
            event_id="evt-2",
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )

        # IDs should be different
        assert event1.id != event2.id

    def test_processed_at_precision(self):
        """Test that processed_at maintains proper datetime precision."""
        event = ProcessedEvent.create_new(
            event_id="evt-123",
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )

        # Should have microsecond precision
        assert event.processed_at.microsecond >= 0
        assert isinstance(event.processed_at, datetime)
