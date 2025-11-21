"""Shipment schemas for client app."""

from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ShipmentInfo(BaseModel):
    """Schema for shipment information associated with an order."""

    shipment_id: UUID
    shipment_status: str
    vehicle_plate: Optional[str] = None
    driver_name: Optional[str] = None
    fecha_entrega_estimada: date
    route_id: Optional[UUID] = None
