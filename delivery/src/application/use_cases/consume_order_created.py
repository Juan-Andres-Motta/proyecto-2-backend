import asyncio
import logging
from datetime import datetime
from uuid import uuid4

from src.application.ports import (
    GeocodingPort,
    ProcessedEventRepositoryPort,
    ShipmentRepositoryPort,
)
from src.domain.entities import ProcessedEvent, Shipment
from src.domain.exceptions import DuplicateEventError, GeocodingError

logger = logging.getLogger(__name__)


class ConsumeOrderCreatedUseCase:
    """Use case for consuming order_created events from SQS."""

    def __init__(
        self,
        shipment_repository: ShipmentRepositoryPort,
        processed_event_repository: ProcessedEventRepositoryPort,
        geocoding_service: GeocodingPort,
    ):
        self._shipment_repo = shipment_repository
        self._processed_event_repo = processed_event_repository
        self._geocoding_service = geocoding_service

    async def execute(
        self,
        event_id: str,
        order_id: str,
        customer_id: str,
        direccion_entrega: str,
        ciudad_entrega: str,
        pais_entrega: str,
        fecha_pedido: datetime,
    ) -> Shipment:
        """
        Process an order_created event.

        Args:
            event_id: Unique event identifier (for idempotency)
            order_id: Order ID
            customer_id: Customer ID
            direccion_entrega: Delivery address
            ciudad_entrega: City
            pais_entrega: Country
            fecha_pedido: Order date

        Returns:
            Created shipment

        Raises:
            DuplicateEventError: If event already processed
        """
        # Check idempotency
        if await self._processed_event_repo.exists(event_id):
            logger.info(f"Event {event_id} already processed, skipping")
            raise DuplicateEventError(event_id)

        # Create shipment
        from uuid import UUID
        shipment = Shipment(
            id=uuid4(),
            order_id=UUID(order_id),
            customer_id=UUID(customer_id),
            direccion_entrega=direccion_entrega,
            ciudad_entrega=ciudad_entrega,
            pais_entrega=pais_entrega,
            fecha_pedido=fecha_pedido,
            fecha_entrega_estimada=Shipment.calculate_estimated_delivery(fecha_pedido),
        )

        # Save shipment
        saved = await self._shipment_repo.save(shipment)
        logger.info(f"Created shipment {saved.id} for order {order_id}")

        # Mark event as processed
        await self._processed_event_repo.save(
            ProcessedEvent(
                id=uuid4(),
                event_id=event_id,
                event_type="order_created",
            )
        )

        # Trigger async geocoding (fire-and-forget)
        asyncio.create_task(self._geocode_shipment(saved))

        return saved

    async def _geocode_shipment(self, shipment: Shipment) -> None:
        """Geocode shipment address asynchronously."""
        try:
            latitude, longitude = await self._geocoding_service.geocode_address(
                shipment.direccion_entrega,
                shipment.ciudad_entrega,
                shipment.pais_entrega,
            )
            shipment.set_coordinates(latitude, longitude)
            await self._shipment_repo.update(shipment)
            logger.info(f"Geocoded shipment {shipment.id}: ({latitude}, {longitude})")
        except GeocodingError as e:
            logger.error(f"Failed to geocode shipment {shipment.id}: {e}")
            shipment.mark_geocoding_failed()
            await self._shipment_repo.update(shipment)
        except Exception as e:
            logger.error(f"Unexpected error geocoding shipment {shipment.id}: {e}")
            shipment.mark_geocoding_failed()
            await self._shipment_repo.update(shipment)
