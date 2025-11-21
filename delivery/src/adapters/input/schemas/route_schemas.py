from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class GenerateRoutesRequest(BaseModel):
    fecha_entrega_estimada: date
    vehicle_ids: List[UUID]


class GenerateRoutesResponse(BaseModel):
    message: str
    fecha_entrega_estimada: date
    num_vehicles: int
    num_pending_shipments: int


class ShipmentInRoute(BaseModel):
    id: UUID
    order_id: UUID
    direccion_entrega: str
    ciudad_entrega: str
    sequence_in_route: int
    shipment_status: str


class RouteResponse(BaseModel):
    id: UUID
    vehicle_id: UUID
    vehicle_plate: Optional[str] = None
    driver_name: Optional[str] = None
    fecha_ruta: date
    estado_ruta: str
    duracion_estimada_minutos: int
    total_distance_km: float
    total_orders: int


class RouteDetailResponse(RouteResponse):
    driver_phone: Optional[str] = None
    shipments: List[ShipmentInRoute] = []


class RouteListResponse(BaseModel):
    items: List[RouteResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool


class RouteStatusUpdateRequest(BaseModel):
    estado_ruta: str = Field(..., pattern="^(en_progreso|completada|cancelada)$")


class RouteStatusUpdateResponse(BaseModel):
    id: UUID
    estado_ruta: str
    message: str
