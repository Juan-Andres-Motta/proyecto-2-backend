"""Warehouse domain entity."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Warehouse:
    """Domain entity for Warehouse."""

    id: UUID
    name: str
    country: str
    city: str
    address: str
    created_at: datetime
    updated_at: datetime
