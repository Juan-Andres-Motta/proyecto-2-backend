from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class ClientCreate(BaseModel):
    cognito_user_id: str
    email: EmailStr
    telefono: str
    nombre_institucion: str
    tipo_institucion: str = Field(
        ...,
        description="Tipo de institución: hospital, clinica, laboratorio, centro_diagnostico"
    )
    nit: str
    direccion: str
    ciudad: str
    pais: str
    representante: str
    vendedor_asignado_id: UUID | None = None


class ClientResponse(BaseModel):
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

    @classmethod
    def from_domain(cls, client) -> "ClientResponse":
        """Map domain entity to DTO."""
        return cls(
            cliente_id=client.cliente_id,
            cognito_user_id=client.cognito_user_id,
            email=client.email,
            telefono=client.telefono,
            nombre_institucion=client.nombre_institucion,
            tipo_institucion=client.tipo_institucion,
            nit=client.nit,
            direccion=client.direccion,
            ciudad=client.ciudad,
            pais=client.pais,
            representante=client.representante,
            vendedor_asignado_id=client.vendedor_asignado_id,
            created_at=client.created_at,
            updated_at=client.updated_at
        )


class ClientListResponse(BaseModel):
    clients: list[ClientResponse]
    total: int


class AssignSellerRequest(BaseModel):
    """Request body for assigning a seller to a client."""
    vendedor_asignado_id: UUID = Field(
        ...,
        description="UUID of the seller to assign to the client"
    )


class AssignSellerResponse(BaseModel):
    """Response after assigning a seller to a client."""
    cliente_id: UUID
    vendedor_asignado_id: UUID
    nombre_institucion: str
    updated_at: datetime

    @classmethod
    def from_domain(cls, client) -> "AssignSellerResponse":
        """Map domain entity to DTO."""
        return cls(
            cliente_id=client.cliente_id,
            vendedor_asignado_id=client.vendedor_asignado_id,
            nombre_institucion=client.nombre_institucion,
            updated_at=client.updated_at
        )
