"""Seller domain entity."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Seller:
    """Domain entity for Seller."""

    id: UUID
    name: str
    email: str
    phone: str
    city: str
    country: str
    created_at: datetime
    updated_at: datetime
