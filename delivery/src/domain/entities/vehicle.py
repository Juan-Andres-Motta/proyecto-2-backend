from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class Vehicle:
    """Vehicle aggregate root."""

    id: UUID
    placa: str
    driver_name: str
    driver_phone: Optional[str] = None
    is_active: bool = True

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        if not self.placa:
            raise ValueError("placa is required")
        if not self.driver_name:
            raise ValueError("driver_name is required")

    def deactivate(self) -> None:
        """Deactivate vehicle (soft delete)."""
        self.is_active = False

    def activate(self) -> None:
        """Activate vehicle."""
        self.is_active = True

    def update(self, driver_name: Optional[str] = None, driver_phone: Optional[str] = None) -> None:
        """Update vehicle information."""
        if driver_name is not None:
            if not driver_name:
                raise ValueError("driver_name cannot be empty")
            self.driver_name = driver_name
        if driver_phone is not None:
            self.driver_phone = driver_phone
