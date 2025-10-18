"""Provider domain entity."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Provider:
    """Domain entity for Provider."""

    id: UUID
    name: str
    nit: str
    contact_name: str
    email: str
    phone: str
    address: str
    country: str
    created_at: datetime
    updated_at: datetime
