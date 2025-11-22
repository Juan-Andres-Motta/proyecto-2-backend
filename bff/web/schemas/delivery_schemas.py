"""
Delivery schemas for web app.

This module contains Pydantic models for delivery service
route management, vehicle management, and shipment tracking.
"""

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


# Route Schemas

class RouteGenerationRequest(BaseModel):
    """Request schema for generating delivery routes."""
    fecha_entrega_estimada: date
    vehicle_ids: List[UUID]


class RouteGenerationResponse(BaseModel):
    """Response schema for route generation."""
    message: str
    fecha_entrega_estimada: date
    num_vehicles: int
    num_pending_shipments: int


class RouteStatusUpdateRequest(BaseModel):
    """Request schema for updating route status."""
    estado_ruta: str  # pendiente, en_progreso, completada, cancelada


class RouteResponse(BaseModel):
    """Response schema for a single route."""
    id: UUID
    fecha_ruta: date
    estado_ruta: str
    vehicle_id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ShipmentInRoute(BaseModel):
    """Schema for shipment information within a route."""
    id: UUID
    order_id: UUID
    shipment_status: str
    delivery_sequence: int


class VehicleInRoute(BaseModel):
    """Schema for vehicle information within a route."""
    id: UUID
    placa: str
    driver_name: str
    driver_phone: Optional[str] = None


class RouteDetailResponse(BaseModel):
    """Response schema for detailed route information."""
    id: UUID
    fecha_ruta: date
    estado_ruta: str
    vehicle_id: UUID
    vehicle: Optional[VehicleInRoute] = None
    shipments: List[ShipmentInRoute] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RoutesListResponse(BaseModel):
    """Response schema for paginated list of routes."""
    items: List[RouteResponse]
    total: int


# Vehicle Schemas

class VehicleCreateRequest(BaseModel):
    """Request schema for creating a vehicle."""
    placa: str
    driver_name: str
    driver_phone: Optional[str] = None


class VehicleUpdateRequest(BaseModel):
    """Request schema for updating a vehicle."""
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None


class VehicleResponse(BaseModel):
    """Response schema for a single vehicle."""
    id: UUID
    placa: str
    driver_name: str
    driver_phone: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class VehiclesListResponse(BaseModel):
    """Response schema for paginated list of vehicles."""
    items: List[VehicleResponse]
    total: int


# Shipment Schemas

class ShipmentStatusUpdateRequest(BaseModel):
    """Request schema for updating shipment status."""
    shipment_status: str  # pendiente, en_ruta, entregado, fallido


class ShipmentResponse(BaseModel):
    """Response schema for a single shipment."""
    id: UUID
    order_id: UUID
    route_id: Optional[UUID] = None
    shipment_status: str
    delivery_sequence: Optional[int] = None
    fecha_entrega_estimada: Optional[date] = None
    updated_at: Optional[datetime] = None
