import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from src.domain.entities import ProcessedEvent


class TestProcessedEventCreation:
    def test_create_valid_processed_event(self):
        """Test creating a valid processed event with required fields."""
        event_id = str(uuid4())
        event_type = "order.created"
        entity_id = uuid4()

        event = ProcessedEvent(
            id=entity_id,
            event_id=event_id,
            event_type=event_type,
        )

        assert event.id == entity_id
        assert event.event_id == event_id
        assert event.event_type == event_type
        assert event.processed_at is None

    def test_create_processed_event_with_timestamp(self):
        """Test creating a processed event with processing timestamp."""
        event_id = str(uuid4())
        event_type = "shipment.delivered"
        processed_at = datetime.now()
        entity_id = uuid4()

        event = ProcessedEvent(
            id=entity_id,
            event_id=event_id,
            event_type=event_type,
            processed_at=processed_at,
        )

        assert event.id == entity_id
        assert event.event_id == event_id
        assert event.event_type == event_type
        assert event.processed_at == processed_at

    def test_create_processed_event_with_different_event_types(self):
        """Test creating processed events with various event types."""
        event_types = [
            "order.created",
            "order.updated",
            "shipment.assigned",
            "shipment.in_transit",
            "shipment.delivered",
            "route.started",
            "route.completed",
            "geocoding.success",
            "geocoding.failed",
        ]

        for event_type in event_types:
            event = ProcessedEvent(
                id=uuid4(),
                event_id=f"{event_type}_{uuid4()}",
                event_type=event_type,
            )

            assert event.event_type == event_type

    def test_create_processed_event_with_uuid_event_id(self):
        """Test creating processed event with UUID as event_id."""
        event_id = str(uuid4())
        event = ProcessedEvent(
            id=uuid4(),
            event_id=event_id,
            event_type="test.event",
        )

        assert event.event_id == event_id

    def test_create_processed_event_with_string_event_id(self):
        """Test creating processed event with string event_id."""
        event_id = "custom-event-id-12345"
        event = ProcessedEvent(
            id=uuid4(),
            event_id=event_id,
            event_type="test.event",
        )

        assert event.event_id == event_id


class TestProcessedEventFields:
    def test_processed_event_with_past_timestamp(self):
        """Test processed event with a timestamp in the past."""
        past_time = datetime.now() - timedelta(hours=1)
        event = ProcessedEvent(
            id=uuid4(),
            event_id="test-event",
            event_type="test.type",
            processed_at=past_time,
        )

        assert event.processed_at == past_time

    def test_processed_event_with_future_timestamp(self):
        """Test processed event with a future timestamp (edge case)."""
        future_time = datetime.now() + timedelta(hours=1)
        event = ProcessedEvent(
            id=uuid4(),
            event_id="test-event",
            event_type="test.type",
            processed_at=future_time,
        )

        assert event.processed_at == future_time

    def test_processed_event_with_explicit_none_processed_at(self):
        """Test creating processed event with explicit None for processed_at."""
        event = ProcessedEvent(
            id=uuid4(),
            event_id="test-event",
            event_type="test.type",
            processed_at=None,
        )

        assert event.processed_at is None

    def test_processed_event_with_very_precise_timestamp(self):
        """Test processed event with microsecond precision timestamp."""
        precise_time = datetime(2025, 1, 15, 14, 30, 45, 123456)
        event = ProcessedEvent(
            id=uuid4(),
            event_id="test-event",
            event_type="test.type",
            processed_at=precise_time,
        )

        assert event.processed_at == precise_time
        assert event.processed_at.microsecond == 123456


class TestProcessedEventIdempotency:
    def test_events_with_same_event_id_different_ids(self):
        """Test that two ProcessedEvent instances can have same event_id but different entity IDs."""
        event_id = "duplicate-event-123"
        event_type = "order.created"

        event1 = ProcessedEvent(
            id=uuid4(),
            event_id=event_id,
            event_type=event_type,
        )

        event2 = ProcessedEvent(
            id=uuid4(),
            event_id=event_id,
            event_type=event_type,
        )

        # Should have same event_id but different entity IDs
        assert event1.event_id == event2.event_id
        assert event1.id != event2.id

    def test_event_id_uniqueness_within_type(self):
        """Test that event_id can be unique within event type."""
        event_type = "shipment.delivered"
        events = []

        for i in range(5):
            event = ProcessedEvent(
                id=uuid4(),
                event_id=f"{event_type}_{i}",
                event_type=event_type,
            )
            events.append(event)

        # All event_ids should be unique
        event_ids = [e.event_id for e in events]
        assert len(event_ids) == len(set(event_ids))


class TestProcessedEventDataclass:
    def test_processed_event_is_dataclass(self):
        """Test that ProcessedEvent behaves as a dataclass."""
        event = ProcessedEvent(
            id=uuid4(),
            event_id="test-event",
            event_type="test.type",
        )

        # Should have __dataclass_fields__ or be convertible to dict-like
        assert hasattr(event, 'id')
        assert hasattr(event, 'event_id')
        assert hasattr(event, 'event_type')
        assert hasattr(event, 'processed_at')

    def test_processed_event_field_access(self):
        """Test direct field access on ProcessedEvent."""
        entity_id = uuid4()
        event_id = "test-event-id"
        event_type = "test.event"
        now = datetime.now()

        event = ProcessedEvent(
            id=entity_id,
            event_id=event_id,
            event_type=event_type,
            processed_at=now,
        )

        # Access all fields
        assert event.id == entity_id
        assert event.event_id == event_id
        assert event.event_type == event_type
        assert event.processed_at == now


class TestProcessedEventEventTypes:
    def test_event_type_with_dots(self):
        """Test event types with dot notation."""
        event_type = "domain.entity.action"
        event = ProcessedEvent(
            id=uuid4(),
            event_id="test-event",
            event_type=event_type,
        )

        assert event.event_type == event_type

    def test_event_type_with_hyphens(self):
        """Test event types with hyphens."""
        event_type = "order-status-changed"
        event = ProcessedEvent(
            id=uuid4(),
            event_id="test-event",
            event_type=event_type,
        )

        assert event.event_type == event_type

    def test_event_type_with_underscores(self):
        """Test event types with underscores."""
        event_type = "shipment_location_updated"
        event = ProcessedEvent(
            id=uuid4(),
            event_id="test-event",
            event_type=event_type,
        )

        assert event.event_type == event_type

    def test_event_type_case_sensitivity(self):
        """Test that event types are case-sensitive."""
        event_type_lower = "order.created"
        event_type_upper = "ORDER.CREATED"

        event1 = ProcessedEvent(
            id=uuid4(),
            event_id="test1",
            event_type=event_type_lower,
        )

        event2 = ProcessedEvent(
            id=uuid4(),
            event_id="test2",
            event_type=event_type_upper,
        )

        assert event1.event_type != event2.event_type


class TestProcessedEventTimestamps:
    def test_processed_event_millisecond_precision(self):
        """Test that ProcessedEvent preserves millisecond precision."""
        time_with_ms = datetime(2025, 1, 15, 10, 30, 45, 500000)
        event = ProcessedEvent(
            id=uuid4(),
            event_id="test-event",
            event_type="test.type",
            processed_at=time_with_ms,
        )

        assert event.processed_at.microsecond == 500000

    def test_processed_event_midnight(self):
        """Test processed event with midnight timestamp."""
        midnight = datetime(2025, 1, 15, 0, 0, 0)
        event = ProcessedEvent(
            id=uuid4(),
            event_id="test-event",
            event_type="test.type",
            processed_at=midnight,
        )

        assert event.processed_at == midnight

    def test_processed_event_end_of_day(self):
        """Test processed event with end-of-day timestamp."""
        end_of_day = datetime(2025, 1, 15, 23, 59, 59, 999999)
        event = ProcessedEvent(
            id=uuid4(),
            event_id="test-event",
            event_type="test.type",
            processed_at=end_of_day,
        )

        assert event.processed_at == end_of_day


class TestProcessedEventEdgeCases:
    def test_processed_event_with_empty_string_event_id(self):
        """Test creating processed event with empty string event_id."""
        event = ProcessedEvent(
            id=uuid4(),
            event_id="",  # Empty string
            event_type="test.type",
        )

        assert event.event_id == ""

    def test_processed_event_with_empty_event_type(self):
        """Test creating processed event with empty event type."""
        event = ProcessedEvent(
            id=uuid4(),
            event_id="test-event",
            event_type="",  # Empty string
        )

        assert event.event_type == ""

    def test_processed_event_with_special_characters_in_event_id(self):
        """Test processed event with special characters in event_id."""
        event_id = "event_id:with:colons@and&symbols#hash"
        event = ProcessedEvent(
            id=uuid4(),
            event_id=event_id,
            event_type="test.type",
        )

        assert event.event_id == event_id

    def test_processed_event_with_very_long_event_id(self):
        """Test processed event with very long event_id."""
        long_event_id = "x" * 1000
        event = ProcessedEvent(
            id=uuid4(),
            event_id=long_event_id,
            event_type="test.type",
        )

        assert event.event_id == long_event_id
        assert len(event.event_id) == 1000

    def test_processed_event_with_very_long_event_type(self):
        """Test processed event with very long event type."""
        long_event_type = ".".join(["segment"] * 100)
        event = ProcessedEvent(
            id=uuid4(),
            event_id="test-event",
            event_type=long_event_type,
        )

        assert event.event_type == long_event_type


class TestProcessedEventRelatedObjects:
    def test_multiple_processed_events_different_timestamps(self):
        """Test creating multiple processed events with incrementing timestamps."""
        events = []
        base_time = datetime(2025, 1, 15, 10, 0, 0)

        for i in range(5):
            event = ProcessedEvent(
                id=uuid4(),
                event_id=f"event_{i}",
                event_type="test.type",
                processed_at=base_time + timedelta(seconds=i),
            )
            events.append(event)

        # Verify all timestamps are different
        timestamps = [e.processed_at for e in events]
        assert len(timestamps) == len(set(timestamps))

    def test_processed_events_from_different_event_sources(self):
        """Test processed events originating from different sources."""
        sources = ["kafka", "sns", "sqs", "api"]
        events = []

        for source in sources:
            event = ProcessedEvent(
                id=uuid4(),
                event_id=f"{source}_{uuid4()}",
                event_type=f"{source}.event",
                processed_at=datetime.now(),
            )
            events.append(event)

        assert len(events) == len(sources)
        assert all(e.event_type.startswith(s) for e, s in zip(events, sources))
