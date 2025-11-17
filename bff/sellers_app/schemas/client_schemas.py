"""Client schemas for sellers app."""

from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class ClientCreateInput(BaseModel):
    """Input schema for creating a client via sellers app."""
    cognito_user_id: str
    email: EmailStr
    telefono: str
    nombre_institucion: str
    tipo_institucion: str
    nit: str
    direccion: str
    ciudad: str
    pais: str
    representante: str
    vendedor_asignado_id: UUID | None = None


class ClientResponse(BaseModel):
    """Response schema for a client."""
    cliente_id: UUID
    cognito_user_id: str
    email: str
    telefono: str
    nombre_institucion: str
    tipo_institucion: str
    nit: str
    direccion: str
    ciudad: str
    pais: str
    representante: str
    vendedor_asignado_id: UUID | None
    created_at: datetime
    updated_at: datetime


class ClientListResponse(BaseModel):
    """Response schema for listing clients."""
    items: List[ClientResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool
