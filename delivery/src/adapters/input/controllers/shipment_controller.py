from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from src.adapters.input.schemas.shipment_schemas import (
    ShipmentResponse,
    ShipmentStatusUpdateRequest,
    ShipmentStatusUpdateResponse,
)
from src.application.use_cases.get_shipment_by_order import GetShipmentByOrderUseCase
from src.application.use_cases.update_shipment_status import UpdateShipmentStatusUseCase
from src.domain.exceptions import EntityNotFoundError, InvalidStatusTransitionError
from src.infrastructure.dependencies import (
    get_get_shipment_by_order_use_case,
    get_update_shipment_status_use_case,
)

router = APIRouter(tags=["Shipments"])


@router.get("/shipments/{order_id}", response_model=ShipmentResponse)
async def get_shipment(
    order_id: UUID,
    use_case: GetShipmentByOrderUseCase = Depends(get_get_shipment_by_order_use_case),
):
    """Get shipment information for Order Service enrichment."""
    try:
        result = await use_case.execute(order_id)
        return ShipmentResponse(
            shipment_id=result["shipment_id"],
            order_id=result["order_id"],
            shipment_status=result["shipment_status"],
            vehicle_plate=result["vehicle_plate"],
            driver_name=result["driver_name"],
            fecha_entrega_estimada=result["fecha_entrega_estimada"],
            route_id=result["route_id"],
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/shipments/{order_id}/status", response_model=ShipmentStatusUpdateResponse)
async def update_shipment_status(
    order_id: UUID,
    request: ShipmentStatusUpdateRequest,
    use_case: UpdateShipmentStatusUseCase = Depends(get_update_shipment_status_use_case),
):
    """Update shipment status (manual by driver/admin)."""
    try:
        shipment = await use_case.execute(order_id, request.shipment_status)
        return ShipmentStatusUpdateResponse(
            shipment_id=shipment.id,
            order_id=shipment.order_id,
            shipment_status=shipment.shipment_status.value,
            message="Shipment status updated successfully",
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
