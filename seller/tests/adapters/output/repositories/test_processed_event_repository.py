"""Unit tests for ProcessedEventRepository."""

from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from src.adapters.output.repositories.processed_event_repository import (
    ProcessedEventRepository,
)
from src.domain.entities.processed_event import ProcessedEvent
from src.infrastructure.database.models import ProcessedEvent as ORMProcessedEvent


@pytest.fixture
def processed_event_repository(db_session):
    """Create repository instance for testing."""
    return ProcessedEventRepository(session=db_session)


@pytest.fixture
def sample_processed_event():
    """Create sample ProcessedEvent domain entity."""
    return ProcessedEvent.create_new(
        event_id="evt-123-abc",
        event_type="order_created",
        microservice="order",
        payload_snapshot='{"order_id": "order-123"}',
    )


@pytest.fixture(autouse=True)
async def clear_processed_events(db_session):
    """Clear order_recived_event table before each test."""
    from sqlalchemy import text

    await db_session.execute(text("DELETE FROM order_recived_event"))
    await db_session.commit()
    yield


class TestHasBeenProcessed:
    """Tests for has_been_processed() method."""

    @pytest.mark.asyncio
    async def test_returns_false_when_event_not_found(
        self, processed_event_repository
    ):
        """Test returns False when event_id doesn't exist."""
        result = await processed_event_repository.has_been_processed("non-existent-id")

        assert result is False

    @pytest.mark.asyncio
    async def test_returns_true_when_event_exists(
        self, processed_event_repository, sample_processed_event, db_session
    ):
        """Test returns True when event_id exists in database."""
        # Save an event first
        orm_event = ORMProcessedEvent(
            id=sample_processed_event.id,
            event_id=sample_processed_event.event_id,
            event_type=sample_processed_event.event_type,
            microservice=sample_processed_event.microservice,
            payload_snapshot=sample_processed_event.payload_snapshot,
            processed_at=sample_processed_event.processed_at,
        )
        db_session.add(orm_event)
        await db_session.commit()

        # Check if processed
        result = await processed_event_repository.has_been_processed(
            sample_processed_event.event_id
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_has_been_processed_is_case_sensitive(
        self, processed_event_repository, sample_processed_event, db_session
    ):
        """Test that event_id comparison is case-sensitive."""
        # Save event
        orm_event = ORMProcessedEvent(
            id=sample_processed_event.id,
            event_id="EVT-123-ABC",
            event_type=sample_processed_event.event_type,
            microservice=sample_processed_event.microservice,
            payload_snapshot=sample_processed_event.payload_snapshot,
            processed_at=sample_processed_event.processed_at,
        )
        db_session.add(orm_event)
        await db_session.commit()

        # Different case should not match
        result = await processed_event_repository.has_been_processed("evt-123-abc")

        assert result is False


class TestMarkAsProcessed:
    """Tests for mark_as_processed() method."""

    @pytest.mark.asyncio
    async def test_mark_as_processed_saves_event(
        self, processed_event_repository, sample_processed_event
    ):
        """Test that mark_as_processed saves event to database."""
        result = await processed_event_repository.mark_as_processed(
            sample_processed_event
        )

        assert result.id == sample_processed_event.id
        assert result.event_id == sample_processed_event.event_id
        assert result.event_type == sample_processed_event.event_type
        assert result.microservice == sample_processed_event.microservice

    @pytest.mark.asyncio
    async def test_mark_as_processed_persists_to_database(
        self, processed_event_repository, sample_processed_event, db_session
    ):
        """Test that saved event is actually in database."""
        await processed_event_repository.mark_as_processed(sample_processed_event)

        # Verify in database
        orm_event = await db_session.get(
            ORMProcessedEvent, sample_processed_event.id
        )

        assert orm_event is not None
        assert orm_event.event_id == sample_processed_event.event_id

    @pytest.mark.asyncio
    async def test_mark_as_processed_raises_on_duplicate(
        self, processed_event_repository, sample_processed_event, db_session
    ):
        """Test that duplicate event_id raises IntegrityError."""
        # Save first event
        await processed_event_repository.mark_as_processed(sample_processed_event)

        # Try to save with same event_id (but different id)
        duplicate = ProcessedEvent.create_new(
            event_id=sample_processed_event.event_id,  # Same event_id
            event_type="order_created",
            microservice="order",
            payload_snapshot='{"duplicate": true}',
        )

        with pytest.raises(IntegrityError):
            await processed_event_repository.mark_as_processed(duplicate)

    @pytest.mark.asyncio
    async def test_mark_as_processed_stores_payload_snapshot(
        self, processed_event_repository
    ):
        """Test that payload_snapshot is properly stored."""
        payload = '{"order_id": "123", "amount": 500.00}'
        event = ProcessedEvent.create_new(
            event_id="evt-test-123",
            event_type="order_created",
            microservice="order",
            payload_snapshot=payload,
        )

        result = await processed_event_repository.mark_as_processed(event)

        assert result.payload_snapshot == payload

    @pytest.mark.asyncio
    async def test_mark_as_processed_stores_timestamp(
        self, processed_event_repository, sample_processed_event
    ):
        """Test that processed_at timestamp is stored."""
        result = await processed_event_repository.mark_as_processed(
            sample_processed_event
        )

        # Verify timestamp is set and matches the input
        assert result.processed_at is not None
        assert result.processed_at == sample_processed_event.processed_at


class TestGetByEventId:
    """Tests for get_by_event_id() method."""

    @pytest.mark.asyncio
    async def test_get_by_event_id_returns_none_when_not_found(
        self, processed_event_repository
    ):
        """Test returns None when event_id doesn't exist."""
        result = await processed_event_repository.get_by_event_id("non-existent-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_event_id_retrieves_event(
        self, processed_event_repository, sample_processed_event, db_session
    ):
        """Test retrieves event when it exists."""
        # Save event first
        orm_event = ORMProcessedEvent(
            id=sample_processed_event.id,
            event_id=sample_processed_event.event_id,
            event_type=sample_processed_event.event_type,
            microservice=sample_processed_event.microservice,
            payload_snapshot=sample_processed_event.payload_snapshot,
            processed_at=sample_processed_event.processed_at,
        )
        db_session.add(orm_event)
        await db_session.commit()

        # Retrieve
        result = await processed_event_repository.get_by_event_id(
            sample_processed_event.event_id
        )

        assert result is not None
        assert result.event_id == sample_processed_event.event_id
        assert result.event_type == sample_processed_event.event_type

    @pytest.mark.asyncio
    async def test_get_by_event_id_returns_complete_entity(
        self, processed_event_repository
    ):
        """Test that all entity fields are properly mapped."""
        event = ProcessedEvent.create_new(
            event_id="evt-complete-123",
            event_type="order_created",
            microservice="order",
            payload_snapshot='{"full": "payload"}',
        )
        await processed_event_repository.mark_as_processed(event)

        result = await processed_event_repository.get_by_event_id("evt-complete-123")

        assert result.id == event.id
        assert result.event_id == "evt-complete-123"
        assert result.event_type == "order_created"
        assert result.microservice == "order"
        assert result.payload_snapshot == '{"full": "payload"}'
        assert result.processed_at is not None


class TestHasBeenProcessedExceptionHandling:
    """Tests for exception handling in has_been_processed() method."""

    @pytest.mark.asyncio
    async def test_has_been_processed_raises_on_database_error(self, processed_event_repository):
        """Test that database errors are raised and not silently caught."""
        from unittest.mock import AsyncMock

        # Mock the session to raise an error
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Database connection error")

        repository = ProcessedEventRepository(session=mock_session)

        with pytest.raises(Exception) as exc_info:
            await repository.has_been_processed("evt-error-123")

        assert "Database connection error" in str(exc_info.value)


class TestMarkAsProcessedExceptionHandling:
    """Tests for exception handling in mark_as_processed() method."""

    @pytest.mark.asyncio
    async def test_mark_as_processed_handles_integrity_error_rollback(
        self, processed_event_repository, sample_processed_event, db_session
    ):
        """Test that IntegrityError causes rollback and is raised."""
        # Save first event
        await processed_event_repository.mark_as_processed(sample_processed_event)

        # Create duplicate with same event_id
        duplicate = ProcessedEvent.create_new(
            event_id=sample_processed_event.event_id,  # Same event_id
            event_type="order_updated",
            microservice="order",
            payload_snapshot='{"duplicate": true}',
        )

        # Should raise IntegrityError and rollback
        with pytest.raises(IntegrityError):
            await processed_event_repository.mark_as_processed(duplicate)

        # Verify only original event is in database
        result = await processed_event_repository.get_by_event_id(
            sample_processed_event.event_id
        )
        assert result.event_type == "order_created"  # Original, not duplicate

    @pytest.mark.asyncio
    async def test_mark_as_processed_handles_generic_exception_rollback(
        self, processed_event_repository, sample_processed_event
    ):
        """Test that generic exceptions cause rollback and are raised."""
        from unittest.mock import AsyncMock

        # Mock session to raise a generic error during commit
        mock_session = AsyncMock()
        mock_session.commit.side_effect = Exception("Unexpected database error")

        repository = ProcessedEventRepository(session=mock_session)

        # Should raise the exception
        with pytest.raises(Exception) as exc_info:
            await repository.mark_as_processed(sample_processed_event)

        assert "Unexpected database error" in str(exc_info.value)
        # Verify rollback was called
        mock_session.rollback.assert_called_once()


class TestGetByEventIdExceptionHandling:
    """Tests for exception handling in get_by_event_id() method."""

    @pytest.mark.asyncio
    async def test_get_by_event_id_raises_on_database_error(
        self, processed_event_repository
    ):
        """Test that database errors are raised and not silently caught."""
        from unittest.mock import AsyncMock

        # Mock the session to raise an error
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Database query failed")

        repository = ProcessedEventRepository(session=mock_session)

        with pytest.raises(Exception) as exc_info:
            await repository.get_by_event_id("evt-error-123")

        assert "Database query failed" in str(exc_info.value)


class TestProcessedEventRepositoryIntegration:
    """Integration tests for repository operations."""

    @pytest.mark.asyncio
    async def test_idempotency_flow(self, processed_event_repository):
        """Test complete idempotency check and mark flow."""
        event_id = "evt-idempotent-123"

        # First check - should not be processed
        is_processed = await processed_event_repository.has_been_processed(event_id)
        assert is_processed is False

        # Mark as processed
        event = ProcessedEvent.create_new(
            event_id=event_id,
            event_type="order_created",
            microservice="order",
            payload_snapshot='{"order_id": "123"}',
        )
        await processed_event_repository.mark_as_processed(event)

        # Second check - should be processed
        is_processed = await processed_event_repository.has_been_processed(event_id)
        assert is_processed is True

        # Retrieve should work
        retrieved = await processed_event_repository.get_by_event_id(event_id)
        assert retrieved is not None
        assert retrieved.event_id == event_id

    @pytest.mark.asyncio
    async def test_multiple_events_independence(self, processed_event_repository):
        """Test that multiple events are tracked independently."""
        event1_id = "evt-1"
        event2_id = "evt-2"

        # Save first event
        event1 = ProcessedEvent.create_new(
            event_id=event1_id,
            event_type="order_created",
            microservice="order",
            payload_snapshot='{"order": 1}',
        )
        await processed_event_repository.mark_as_processed(event1)

        # Save second event
        event2 = ProcessedEvent.create_new(
            event_id=event2_id,
            event_type="order_created",
            microservice="order",
            payload_snapshot='{"order": 2}',
        )
        await processed_event_repository.mark_as_processed(event2)

        # Both should be findable
        assert await processed_event_repository.has_been_processed(event1_id) is True
        assert await processed_event_repository.has_been_processed(event2_id) is True

        # Retrieve should return correct data
        retrieved1 = await processed_event_repository.get_by_event_id(event1_id)
        retrieved2 = await processed_event_repository.get_by_event_id(event2_id)

        assert '{"order": 1}' in retrieved1.payload_snapshot
        assert '{"order": 2}' in retrieved2.payload_snapshot
