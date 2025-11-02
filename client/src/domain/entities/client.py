"""Client domain entity."""
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID


@dataclass
class Client:
    """Domain entity for Client."""

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

    def assign_seller(self, vendedor_id: UUID) -> None:
        """Assign a seller to this client.

        Args:
            vendedor_id: UUID of the seller to assign
        """
        self.vendedor_asignado_id = vendedor_id
        self.updated_at = datetime.now(timezone.utc)
