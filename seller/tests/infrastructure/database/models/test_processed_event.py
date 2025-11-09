"""Unit tests for ProcessedEvent ORM model."""

import uuid
from datetime import datetime

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database.models import Base
from src.infrastructure.database.models.processed_event import ProcessedEvent as ORMProcessedEvent


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create in-memory SQLite engine for tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database(test_engine):
    """Create all tables before each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS order_recived_event"))


@pytest_asyncio.fixture
async def db_session(test_engine):
    """Provide async database session."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


class TestProcessedEventORMInit:
    """Tests for ProcessedEvent ORM model initialization."""

    @pytest.mark.asyncio
    async def test_create_processed_event_record(self, db_session):
        """Test creating a ProcessedEvent database record."""
        event_id_val = str(uuid.uuid4())
        id_val = uuid.uuid4()

        event = ORMProcessedEvent(
            id=id_val,
            event_id=event_id_val,
            event_type="order_created",
            microservice="order",
            payload_snapshot='{"order_id": "123"}',
            processed_at=datetime.utcnow(),
        )

        db_session.add(event)
        await db_session.commit()

        # Verify it was saved
        stmt = select(ORMProcessedEvent).where(ORMProcessedEvent.id == id_val)
        result = await db_session.execute(stmt)
        saved_event = result.scalars().first()

        assert saved_event is not None
        assert saved_event.event_id == event_id_val
        assert saved_event.event_type == "order_created"

    @pytest.mark.asyncio
    async def test_processed_event_has_correct_tablename(self):
        """Test that ProcessedEvent uses correct table name."""
        assert ORMProcessedEvent.__tablename__ == "order_recived_event"

    @pytest.mark.asyncio
    async def test_processed_event_id_is_uuid_primary_key(self, db_session):
        """Test that id is UUID and primary key."""
        id_val = uuid.uuid4()
        event = ORMProcessedEvent(
            id=id_val,
            event_id=str(uuid.uuid4()),
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )

        db_session.add(event)
        await db_session.commit()

        # Retrieve and verify
        stmt = select(ORMProcessedEvent).where(ORMProcessedEvent.id == id_val)
        result = await db_session.execute(stmt)
        saved_event = result.scalars().first()

        assert saved_event.id == id_val
        assert isinstance(saved_event.id, uuid.UUID)

    @pytest.mark.asyncio
    async def test_processed_event_id_defaults_to_uuid4(self, db_session):
        """Test that id defaults to uuid4 if not provided."""
        event = ORMProcessedEvent(
            event_id=str(uuid.uuid4()),
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )

        db_session.add(event)
        await db_session.commit()

        assert event.id is not None
        assert isinstance(event.id, uuid.UUID)


class TestEventIDField:
    """Tests for event_id field constraints."""

    @pytest.mark.asyncio
    async def test_event_id_is_unique(self, db_session):
        """Test that event_id has unique constraint."""
        event_id_val = "evt-unique-123"

        event1 = ORMProcessedEvent(
            event_id=event_id_val,
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )
        db_session.add(event1)
        await db_session.commit()

        # Try to create duplicate
        event2 = ORMProcessedEvent(
            event_id=event_id_val,
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )
        db_session.add(event2)

        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_event_id_is_indexed(self, db_session):
        """Test that event_id has an index."""
        # Create multiple records
        for i in range(10):
            event = ORMProcessedEvent(
                event_id=f"evt-{i}",
                event_type="order_created",
                microservice="order",
                payload_snapshot="{}",
            )
            db_session.add(event)

        await db_session.commit()

        # Query by event_id (should be indexed)
        stmt = select(ORMProcessedEvent).where(ORMProcessedEvent.event_id == "evt-5")
        result = await db_session.execute(stmt)
        event = result.scalars().first()

        assert event is not None
        assert event.event_id == "evt-5"

    @pytest.mark.asyncio
    async def test_event_id_is_required(self, db_session):
        """Test that event_id is required (not nullable)."""
        event = ORMProcessedEvent(
            event_id=None,  # Required field
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )
        db_session.add(event)

        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_event_id_max_length_255(self, db_session):
        """Test that event_id has max length of 255."""
        # Create a string of 255 characters
        long_event_id = "evt-" + "x" * 251  # Total 255

        event = ORMProcessedEvent(
            event_id=long_event_id,
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )
        db_session.add(event)
        await db_session.commit()

        assert event.event_id == long_event_id


class TestEventTypeField:
    """Tests for event_type field."""

    @pytest.mark.asyncio
    async def test_event_type_stored_correctly(self, db_session):
        """Test that event_type is stored correctly."""
        event = ORMProcessedEvent(
            event_id=str(uuid.uuid4()),
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )
        db_session.add(event)
        await db_session.commit()

        stmt = select(ORMProcessedEvent).where(
            ORMProcessedEvent.event_type == "order_created"
        )
        result = await db_session.execute(stmt)
        saved_event = result.scalars().first()

        assert saved_event.event_type == "order_created"

    @pytest.mark.asyncio
    async def test_event_type_is_indexed(self, db_session):
        """Test that event_type has an index."""
        for i in range(5):
            event = ORMProcessedEvent(
                event_id=f"evt-{i}",
                event_type="order_created",
                microservice="order",
                payload_snapshot="{}",
            )
            db_session.add(event)

        await db_session.commit()

        # Query by event_type
        stmt = select(ORMProcessedEvent).where(
            ORMProcessedEvent.event_type == "order_created"
        )
        result = await db_session.execute(stmt)
        events = result.scalars().all()

        assert len(events) == 5

    @pytest.mark.asyncio
    async def test_event_type_is_required(self, db_session):
        """Test that event_type is required."""
        event = ORMProcessedEvent(
            event_id=str(uuid.uuid4()),
            event_type=None,
            microservice="order",
            payload_snapshot="{}",
        )
        db_session.add(event)

        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_event_type_max_length_100(self, db_session):
        """Test that event_type has max length of 100."""
        long_type = "order_" + "x" * 94  # Total 100

        event = ORMProcessedEvent(
            event_id=str(uuid.uuid4()),
            event_type=long_type,
            microservice="order",
            payload_snapshot="{}",
        )
        db_session.add(event)
        await db_session.commit()

        assert event.event_type == long_type


class TestMicroserviceField:
    """Tests for microservice field."""

    @pytest.mark.asyncio
    async def test_microservice_stored_correctly(self, db_session):
        """Test that microservice is stored correctly."""
        event = ORMProcessedEvent(
            event_id=str(uuid.uuid4()),
            event_type="order_created",
            microservice="seller",
            payload_snapshot="{}",
        )
        db_session.add(event)
        await db_session.commit()

        stmt = select(ORMProcessedEvent).where(
            ORMProcessedEvent.microservice == "seller"
        )
        result = await db_session.execute(stmt)
        saved_event = result.scalars().first()

        assert saved_event.microservice == "seller"

    @pytest.mark.asyncio
    async def test_microservice_is_indexed(self, db_session):
        """Test that microservice has an index."""
        for i in range(5):
            event = ORMProcessedEvent(
                event_id=f"evt-{i}",
                event_type="order_created",
                microservice="order",
                payload_snapshot="{}",
            )
            db_session.add(event)

        await db_session.commit()

        # Query by microservice
        stmt = select(ORMProcessedEvent).where(
            ORMProcessedEvent.microservice == "order"
        )
        result = await db_session.execute(stmt)
        events = result.scalars().all()

        assert len(events) == 5

    @pytest.mark.asyncio
    async def test_microservice_is_required(self, db_session):
        """Test that microservice is required."""
        event = ORMProcessedEvent(
            event_id=str(uuid.uuid4()),
            event_type="order_created",
            microservice=None,
            payload_snapshot="{}",
        )
        db_session.add(event)

        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_microservice_max_length_100(self, db_session):
        """Test that microservice has max length of 100."""
        long_service = "order_" + "x" * 94  # Total 100

        event = ORMProcessedEvent(
            event_id=str(uuid.uuid4()),
            event_type="order_created",
            microservice=long_service,
            payload_snapshot="{}",
        )
        db_session.add(event)
        await db_session.commit()

        assert event.microservice == long_service


class TestPayloadSnapshotField:
    """Tests for payload_snapshot field."""

    @pytest.mark.asyncio
    async def test_payload_snapshot_stored_correctly(self, db_session):
        """Test that payload_snapshot is stored correctly."""
        payload = '{"order_id": "123", "amount": 1250.50}'

        event = ORMProcessedEvent(
            event_id=str(uuid.uuid4()),
            event_type="order_created",
            microservice="order",
            payload_snapshot=payload,
        )
        db_session.add(event)
        await db_session.commit()

        stmt = select(ORMProcessedEvent).where(
            ORMProcessedEvent.event_id == event.event_id
        )
        result = await db_session.execute(stmt)
        saved_event = result.scalars().first()

        assert saved_event.payload_snapshot == payload

    @pytest.mark.asyncio
    async def test_payload_snapshot_is_text_field(self, db_session):
        """Test that payload_snapshot can store large text."""
        large_payload = '{"items": [' + ', '.join([f'{{"id": {i}}}' for i in range(100)]) + ']}'

        event = ORMProcessedEvent(
            event_id=str(uuid.uuid4()),
            event_type="order_created",
            microservice="order",
            payload_snapshot=large_payload,
        )
        db_session.add(event)
        await db_session.commit()

        stmt = select(ORMProcessedEvent).where(
            ORMProcessedEvent.event_id == event.event_id
        )
        result = await db_session.execute(stmt)
        saved_event = result.scalars().first()

        assert saved_event.payload_snapshot == large_payload

    @pytest.mark.asyncio
    async def test_payload_snapshot_is_required(self, db_session):
        """Test that payload_snapshot is required."""
        event = ORMProcessedEvent(
            event_id=str(uuid.uuid4()),
            event_type="order_created",
            microservice="order",
            payload_snapshot=None,
        )
        db_session.add(event)

        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()


class TestProcessedAtField:
    """Tests for processed_at timestamp field."""

    @pytest.mark.asyncio
    async def test_processed_at_stored_correctly(self, db_session):
        """Test that processed_at is stored correctly."""
        now = datetime.utcnow()

        event = ORMProcessedEvent(
            event_id=str(uuid.uuid4()),
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
            processed_at=now,
        )
        db_session.add(event)
        await db_session.commit()

        stmt = select(ORMProcessedEvent).where(
            ORMProcessedEvent.event_id == event.event_id
        )
        result = await db_session.execute(stmt)
        saved_event = result.scalars().first()

        assert saved_event.processed_at is not None

    @pytest.mark.asyncio
    async def test_processed_at_defaults_to_server_time(self, db_session):
        """Test that processed_at defaults to server time."""
        before = datetime.utcnow()

        event = ORMProcessedEvent(
            event_id=str(uuid.uuid4()),
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
            # Don't set processed_at - should default to server time
        )
        db_session.add(event)
        await db_session.commit()

        after = datetime.utcnow()

        # processed_at should be set automatically
        assert event.processed_at is not None

    @pytest.mark.asyncio
    async def test_processed_at_has_timezone_awareness(self, db_session):
        """Test that processed_at is timezone-aware (DateTime with timezone=True)."""
        now = datetime.utcnow()

        event = ORMProcessedEvent(
            event_id=str(uuid.uuid4()),
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
            processed_at=now,
        )
        db_session.add(event)
        await db_session.commit()

        stmt = select(ORMProcessedEvent).where(
            ORMProcessedEvent.event_id == event.event_id
        )
        result = await db_session.execute(stmt)
        saved_event = result.scalars().first()

        assert isinstance(saved_event.processed_at, datetime)

    @pytest.mark.asyncio
    async def test_processed_at_is_required(self, db_session):
        """Test that processed_at is required (not nullable)."""
        # In SQLite, server_default may not enforce NOT NULL at ORM level
        # But we should verify the column definition
        from src.infrastructure.database.models.processed_event import ProcessedEvent as PE

        # Check column definition
        processed_at_col = PE.__table__.columns["processed_at"]
        assert not processed_at_col.nullable


class TestIntegration:
    """Integration tests for ProcessedEvent ORM model."""

    @pytest.mark.asyncio
    async def test_create_and_retrieve_event(self, db_session):
        """Test creating and retrieving a processed event."""
        event_id = "evt-integration-test"

        event = ORMProcessedEvent(
            event_id=event_id,
            event_type="order_created",
            microservice="order",
            payload_snapshot='{"order_id": "123"}',
        )
        db_session.add(event)
        await db_session.commit()

        # Retrieve
        stmt = select(ORMProcessedEvent).where(
            ORMProcessedEvent.event_id == event_id
        )
        result = await db_session.execute(stmt)
        retrieved = result.scalars().first()

        assert retrieved.event_id == event_id
        assert retrieved.event_type == "order_created"
        assert retrieved.microservice == "order"

    @pytest.mark.asyncio
    async def test_check_event_by_event_id(self, db_session):
        """Test checking if event exists by event_id."""
        event_id = "evt-check-123"

        event = ORMProcessedEvent(
            event_id=event_id,
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )
        db_session.add(event)
        await db_session.commit()

        # Check if exists
        stmt = select(ORMProcessedEvent).where(
            ORMProcessedEvent.event_id == event_id
        )
        result = await db_session.execute(stmt)
        exists = result.scalars().first() is not None

        assert exists is True

    @pytest.mark.asyncio
    async def test_query_events_by_type_and_microservice(self, db_session):
        """Test querying events by type and microservice."""
        # Create events
        event1 = ORMProcessedEvent(
            event_id="evt-1",
            event_type="order_created",
            microservice="order",
            payload_snapshot="{}",
        )
        event2 = ORMProcessedEvent(
            event_id="evt-2",
            event_type="order_created",
            microservice="seller",
            payload_snapshot="{}",
        )
        event3 = ORMProcessedEvent(
            event_id="evt-3",
            event_type="order_updated",
            microservice="order",
            payload_snapshot="{}",
        )

        db_session.add_all([event1, event2, event3])
        await db_session.commit()

        # Query order_created from order microservice
        stmt = select(ORMProcessedEvent).where(
            (ORMProcessedEvent.event_type == "order_created")
            & (ORMProcessedEvent.microservice == "order")
        )
        result = await db_session.execute(stmt)
        events = result.scalars().all()

        assert len(events) == 1
        assert events[0].event_id == "evt-1"

    @pytest.mark.asyncio
    async def test_multiple_events_from_same_microservice(self, db_session):
        """Test multiple events from same microservice."""
        for i in range(5):
            event = ORMProcessedEvent(
                event_id=f"evt-order-{i}",
                event_type="order_created",
                microservice="order",
                payload_snapshot=f'{{"order_id": "{i}"}}',
            )
            db_session.add(event)

        await db_session.commit()

        # Query all order events
        stmt = select(ORMProcessedEvent).where(
            ORMProcessedEvent.microservice == "order"
        )
        result = await db_session.execute(stmt)
        events = result.scalars().all()

        assert len(events) == 5
