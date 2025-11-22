from uuid import UUID

from src.application.ports import ShipmentRepositoryPort
from src.domain.entities import Shipment
from src.domain.exceptions import EntityNotFoundError, InvalidStatusTransitionError
from src.domain.value_objects import ShipmentStatus


class UpdateShipmentStatusUseCase:
    """Use case for updating shipment status."""

    def __init__(self, shipment_repository: ShipmentRepositoryPort):
        self._shipment_repo = shipment_repository

    async def execute(self, order_id: UUID, new_status: str) -> Shipment:
        """
        Update shipment status.

        Args:
            order_id: Order ID
            new_status: New status value

        Returns:
            Updated shipment

        Raises:
            EntityNotFoundError: If shipment not found
            InvalidStatusTransitionError: If transition is invalid
        """
        shipment = await self._shipment_repo.find_by_order_id(order_id)
        if not shipment:
            raise EntityNotFoundError("Shipment", str(order_id))

        target_status = ShipmentStatus(new_status)

        # Apply status transition
        if target_status == ShipmentStatus.IN_TRANSIT:
            shipment.mark_in_transit()
        elif target_status == ShipmentStatus.DELIVERED:
            shipment.mark_delivered()
        else:
            raise InvalidStatusTransitionError(
                "Shipment",
                shipment.shipment_status.value,
                new_status,
            )

        await self._shipment_repo.update(shipment)
        return shipment
