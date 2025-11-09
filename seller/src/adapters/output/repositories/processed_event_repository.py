"""Repository implementation for processed events."""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.processed_event_repository_port import (
    ProcessedEventRepositoryPort,
)
from src.domain.entities.processed_event import ProcessedEvent as DomainProcessedEvent
from src.infrastructure.database.models import ProcessedEvent as ORMProcessedEvent

logger = logging.getLogger(__name__)


class ProcessedEventRepository(ProcessedEventRepositoryPort):
    """PostgreSQL implementation of ProcessedEventRepositoryPort."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def has_been_processed(self, event_id: str) -> bool:
        """
        Check if an event has already been processed.

        Args:
            event_id: Unique event identifier

        Returns:
            True if event exists in database, False otherwise
        """
        logger.debug(f"DB: Checking if event has been processed: event_id={event_id}")

        try:
            stmt = select(ORMProcessedEvent).where(
                ORMProcessedEvent.event_id == event_id
            )
            result = await self.session.execute(stmt)
            exists = result.scalars().first() is not None

            logger.debug(
                f"DB: Event processed check result: event_id={event_id}, exists={exists}"
            )
            return exists

        except Exception as e:
            logger.error(
                f"DB: Error checking if event processed: event_id={event_id}, error={e}"
            )
            raise

    async def mark_as_processed(
        self, processed_event: DomainProcessedEvent
    ) -> DomainProcessedEvent:
        """
        Mark an event as processed by saving it to the database.

        Args:
            processed_event: ProcessedEvent domain entity

        Returns:
            Saved ProcessedEvent entity

        Raises:
            IntegrityError: If event_id already exists (duplicate)
        """
        logger.debug(
            f"DB: Marking event as processed: "
            f"event_id={processed_event.event_id}, "
            f"event_type={processed_event.event_type}"
        )

        try:
            orm_event = ORMProcessedEvent(
                id=processed_event.id,
                event_id=processed_event.event_id,
                event_type=processed_event.event_type,
                microservice=processed_event.microservice,
                payload_snapshot=processed_event.payload_snapshot,
                processed_at=processed_event.processed_at,
            )

            self.session.add(orm_event)
            await self.session.commit()
            await self.session.refresh(orm_event)

            logger.debug(
                f"DB: Successfully marked event as processed: "
                f"event_id={processed_event.event_id}"
            )
            return self._to_domain(orm_event)

        except IntegrityError as e:
            logger.warning(
                f"DB: Event already processed (duplicate): "
                f"event_id={processed_event.event_id}"
            )
            await self.session.rollback()
            raise

        except Exception as e:
            logger.error(
                f"DB: Error marking event as processed: "
                f"event_id={processed_event.event_id}, error={e}"
            )
            await self.session.rollback()
            raise

    async def get_by_event_id(self, event_id: str) -> Optional[DomainProcessedEvent]:
        """
        Get a processed event by its event ID.

        Args:
            event_id: Unique event identifier

        Returns:
            ProcessedEvent domain entity if found, None otherwise
        """
        logger.debug(f"DB: Getting processed event: event_id={event_id}")

        try:
            stmt = select(ORMProcessedEvent).where(
                ORMProcessedEvent.event_id == event_id
            )
            result = await self.session.execute(stmt)
            orm_event = result.scalars().first()

            if orm_event is None:
                logger.debug(f"DB: Processed event not found: event_id={event_id}")
                return None

            logger.debug(
                f"DB: Successfully retrieved processed event: event_id={event_id}"
            )
            return self._to_domain(orm_event)

        except Exception as e:
            logger.error(
                f"DB: Error getting processed event: event_id={event_id}, error={e}"
            )
            raise

    @staticmethod
    def _to_domain(orm_event: ORMProcessedEvent) -> DomainProcessedEvent:
        """Map ORM model to domain entity."""
        return DomainProcessedEvent(
            id=orm_event.id,
            event_id=orm_event.event_id,
            event_type=orm_event.event_type,
            microservice=orm_event.microservice,
            payload_snapshot=orm_event.payload_snapshot,
            processed_at=orm_event.processed_at,
        )
