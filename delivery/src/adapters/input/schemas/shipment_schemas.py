from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ShipmentResponse(BaseModel):
    shipment_id: UUID
    order_id: UUID
    shipment_status: str
    vehicle_plate: Optional[str] = None
    driver_name: Optional[str] = None
    fecha_entrega_estimada: date
    route_id: Optional[UUID] = None


class ShipmentStatusUpdateRequest(BaseModel):
    shipment_status: str = Field(..., pattern="^(in_transit|delivered)$")


class ShipmentStatusUpdateResponse(BaseModel):
    shipment_id: UUID
    order_id: UUID
    shipment_status: str
    message: str
