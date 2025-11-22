from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import List

from src.domain.entities import Shipment, Vehicle


@dataclass
class RouteOptimizationResult:
    """Result of route optimization for a single vehicle."""

    vehicle: Vehicle
    shipments: List[Shipment]  # Ordered by delivery sequence
    total_distance_km: Decimal
    estimated_duration_minutes: int


class RouteOptimizationPort(ABC):
    """
    Port for route optimization strategy.

    Implements Strategy Pattern to allow different optimization algorithms.
    """

    @abstractmethod
    async def optimize_routes(
        self,
        shipments: List[Shipment],
        vehicles: List[Vehicle],
    ) -> List[RouteOptimizationResult]:
        """
        Optimize routes for given shipments and vehicles.

        Args:
            shipments: List of shipments to assign (must have valid coordinates)
            vehicles: List of available vehicles

        Returns:
            List of optimization results, one per vehicle
        """
        pass
