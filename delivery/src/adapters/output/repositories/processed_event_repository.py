from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports import ProcessedEventRepositoryPort
from src.domain.entities import ProcessedEvent
from src.infrastructure.database.models import ProcessedEventModel


class SQLAlchemyProcessedEventRepository(ProcessedEventRepositoryPort):
    """SQLAlchemy implementation of processed event repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, event: ProcessedEvent) -> ProcessedEvent:
        """Save a processed event."""
        model = ProcessedEventModel(
            id=event.id if event.id else uuid4(),
            event_id=event.event_id,
            event_type=event.event_type,
        )
        self._session.add(model)
        await self._session.flush()

        return ProcessedEvent(
            id=model.id,
            event_id=model.event_id,
            event_type=model.event_type,
            processed_at=model.processed_at,
        )

    async def exists(self, event_id: str) -> bool:
        """Check if an event has been processed."""
        result = await self._session.execute(
            select(ProcessedEventModel.id).where(
                ProcessedEventModel.event_id == event_id
            )
        )
        return result.scalar_one_or_none() is not None
