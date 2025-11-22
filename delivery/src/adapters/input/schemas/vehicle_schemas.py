from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class VehicleCreateRequest(BaseModel):
    placa: str
    driver_name: str
    driver_phone: Optional[str] = None


class VehicleUpdateRequest(BaseModel):
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None


class VehicleResponse(BaseModel):
    id: UUID
    placa: str
    driver_name: str
    driver_phone: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class VehicleListResponse(BaseModel):
    items: List[VehicleResponse]
    total: int
