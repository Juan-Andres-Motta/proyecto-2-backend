"""Visit domain entity."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID


class VisitStatus(str, Enum):
    """Visit status enumeration."""

    PROGRAMADA = "programada"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"


@dataclass
class Visit:
    """Domain entity for Visit.

    Represents a scheduled visit from a seller to a client institution.
    Client information is denormalized to preserve historical accuracy.
    """

    id: UUID
    seller_id: UUID
    client_id: UUID
    fecha_visita: datetime  # timezone-aware datetime
    status: VisitStatus
    notas_visita: Optional[str]
    recomendaciones: Optional[str]
    archivos_evidencia: Optional[str]  # Single S3 URL
    client_nombre_institucion: str  # Denormalized
    client_direccion: str  # Denormalized
    client_ciudad: str  # Denormalized
    client_pais: str  # Denormalized
    created_at: datetime
    updated_at: datetime
