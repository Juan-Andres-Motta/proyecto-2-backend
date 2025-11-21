from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional
from uuid import UUID

from src.domain.entities import Route


class RouteRepositoryPort(ABC):
    """Port for route repository operations."""

    @abstractmethod
    async def save(self, route: Route) -> Route:
        """Save a route with its shipments."""
        pass

    @abstractmethod
    async def find_by_id(self, route_id: UUID) -> Optional[Route]:
        """Find a route by ID with shipments."""
        pass

    @abstractmethod
    async def find_by_date(self, fecha_ruta: date) -> List[Route]:
        """Find all routes for a specific date."""
        pass

    @abstractmethod
    async def find_by_date_and_status(
        self, fecha_ruta: date, estado_ruta: str
    ) -> List[Route]:
        """Find routes by date and status."""
        pass

    @abstractmethod
    async def find_all(
        self,
        fecha_ruta: Optional[date] = None,
        estado_ruta: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Route], int]:
        """Find routes with pagination and filters."""
        pass

    @abstractmethod
    async def update(self, route: Route) -> Route:
        """Update a route."""
        pass
