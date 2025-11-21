import logging
from decimal import Decimal
from typing import List

import numpy as np
from sklearn.cluster import KMeans

from src.application.ports.route_optimization_port import (
    RouteOptimizationPort,
    RouteOptimizationResult,
)
from src.domain.entities import Shipment, Vehicle

logger = logging.getLogger(__name__)


class GreedyRouteOptimizer(RouteOptimizationPort):
    """
    Greedy route optimization using K-means clustering and nearest-neighbor.

    Algorithm:
    1. Cluster shipments into K groups (K = number of vehicles) using K-means
    2. Assign each cluster to a vehicle
    3. Order stops within each cluster using nearest-neighbor heuristic
    4. Calculate total distance and estimated duration

    Complexity: O(n * k * i) for clustering + O(n^2) for ordering
    where n = shipments, k = clusters, i = iterations
    """

    # Configuration
    AVG_SPEED_KMH = 30  # Average speed in urban areas
    TIME_PER_STOP_MIN = 5  # Time to deliver at each stop

    async def optimize_routes(
        self,
        shipments: List[Shipment],
        vehicles: List[Vehicle],
    ) -> List[RouteOptimizationResult]:
        """Optimize routes using greedy algorithm."""

        if not shipments:
            logger.warning("No shipments to optimize")
            return []

        if not vehicles:
            raise ValueError("At least one vehicle is required")

        # Filter shipments with valid coordinates
        valid_shipments = [s for s in shipments if s.is_geocoded]
        invalid_count = len(shipments) - len(valid_shipments)

        if invalid_count > 0:
            logger.warning(
                f"Excluding {invalid_count} shipments without coordinates"
            )

        if not valid_shipments:
            logger.warning("No shipments with valid coordinates")
            return []

        logger.info(
            f"Optimizing routes for {len(valid_shipments)} shipments "
            f"and {len(vehicles)} vehicles"
        )

        # Step 1: Cluster shipments
        clusters = self._cluster_shipments(valid_shipments, len(vehicles))

        # Step 2: Order each cluster and create results
        results = []
        for i, cluster in enumerate(clusters):
            if not cluster:
                continue

            vehicle = vehicles[i]

            # Order stops using nearest-neighbor
            ordered = self._nearest_neighbor_order(cluster)

            # Calculate metrics
            distance = self._calculate_total_distance(ordered)
            duration = self._estimate_duration(ordered, distance)

            results.append(RouteOptimizationResult(
                vehicle=vehicle,
                shipments=ordered,
                total_distance_km=Decimal(str(round(distance, 2))),
                estimated_duration_minutes=duration,
            ))

            logger.info(
                f"Route for {vehicle.placa}: "
                f"{len(ordered)} stops, "
                f"{distance:.2f} km, "
                f"{duration} min"
            )

        return results

    def _cluster_shipments(
        self,
        shipments: List[Shipment],
        n_clusters: int,
    ) -> List[List[Shipment]]:
        """
        Cluster shipments using K-means on coordinates.

        Returns list of clusters, each containing shipments.
        """
        if len(shipments) <= n_clusters:
            # One shipment per cluster (or empty clusters)
            clusters = [[s] for s in shipments]
            while len(clusters) < n_clusters:
                clusters.append([])
            return clusters

        # Extract coordinates for clustering
        coords = np.array([
            [float(s.latitude), float(s.longitude)]
            for s in shipments
        ])

        # Run K-means
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(coords)

        # Group shipments by cluster
        clusters = [[] for _ in range(n_clusters)]
        for i, shipment in enumerate(shipments):
            clusters[labels[i]].append(shipment)

        return clusters

    def _nearest_neighbor_order(
        self,
        shipments: List[Shipment],
    ) -> List[Shipment]:
        """
        Order shipments using nearest-neighbor heuristic.

        Starts at first shipment and always moves to nearest unvisited.
        """
        if len(shipments) <= 1:
            return shipments

        ordered = [shipments[0]]
        remaining = set(range(1, len(shipments)))

        while remaining:
            current = ordered[-1]
            nearest_idx = None
            nearest_dist = float('inf')

            for idx in remaining:
                dist = current.coordinates.distance_to(
                    shipments[idx].coordinates
                )
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest_idx = idx

            ordered.append(shipments[nearest_idx])
            remaining.remove(nearest_idx)

        return ordered

    def _calculate_total_distance(self, shipments: List[Shipment]) -> float:
        """Calculate total distance between consecutive stops in km."""
        if len(shipments) <= 1:
            return 0.0

        total = 0.0
        for i in range(len(shipments) - 1):
            total += shipments[i].coordinates.distance_to(
                shipments[i + 1].coordinates
            )

        return total

    def _estimate_duration(
        self,
        shipments: List[Shipment],
        total_distance_km: float,
    ) -> int:
        """
        Estimate total duration in minutes.

        Formula: (distance / speed * 60) + (stops * time_per_stop)
        """
        driving_time = (total_distance_km / self.AVG_SPEED_KMH) * 60
        stop_time = len(shipments) * self.TIME_PER_STOP_MIN

        return int(driving_time + stop_time)
