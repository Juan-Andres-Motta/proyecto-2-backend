import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.adapters.output.repositories.processed_event_repository import SQLAlchemyProcessedEventRepository
from src.domain.entities import ProcessedEvent


class TestSQLAlchemyProcessedEventRepository:
    @pytest.fixture
    def mock_session(self):
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def repository(self, mock_session):
        return SQLAlchemyProcessedEventRepository(mock_session)

    @pytest.mark.asyncio
    async def test_save_event(self, repository, mock_session):
        event = ProcessedEvent(
            id=uuid4(),
            event_id="evt-123",
            event_type="order_created",
        )

        mock_model = MagicMock()
        mock_model.id = event.id
        mock_model.event_id = event.event_id
        mock_model.event_type = event.event_type
        mock_model.processed_at = None

        result = await repository.save(event)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_exists_true(self, repository, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = uuid4()
        mock_session.execute.return_value = mock_result

        result = await repository.exists("evt-123")

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self, repository, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.exists("evt-123")

        assert result is False
