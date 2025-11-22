"""
Delivery controller for web application.

This controller handles route management, vehicle management, and shipment tracking
endpoints for the web admin interface using the delivery port for communication
with the Delivery microservice.
"""

import logging
from datetime import date
from typing import Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from common.auth.dependencies import require_web_user
from common.error_schemas import (
    NotFoundErrorResponse,
    ServiceUnavailableErrorResponse,
    ValidationErrorResponse,
)
from common.exceptions import (
    MicroserviceConnectionError,
    MicroserviceHTTPError,
    MicroserviceValidationError,
)
from dependencies import get_web_delivery_port
from web.ports.delivery_port import DeliveryPort
from web.schemas.delivery_schemas import (
    RouteDetailResponse,
    RouteGenerationRequest,
    RouteGenerationResponse,
    RouteResponse,
    RoutesListResponse,
    RouteStatusUpdateRequest,
    ShipmentResponse,
    ShipmentStatusUpdateRequest,
    VehicleCreateRequest,
    VehicleResponse,
    VehiclesListResponse,
    VehicleUpdateRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["delivery"])


# Routes Management Endpoints

@router.post(
    "/routes/generate",
    response_model=RouteGenerationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"description": "Route generation job accepted"},
        400: {"description": "Invalid request data", "model": ValidationErrorResponse},
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Requires web_users group"},
        503: {"description": "Delivery service unavailable", "model": ServiceUnavailableErrorResponse},
    },
)
async def generate_routes(
    request: RouteGenerationRequest,
    port: DeliveryPort = Depends(get_web_delivery_port),
    user: Dict = Depends(require_web_user),
):
    """
    Trigger route generation for a specific date.

    This endpoint initiates an asynchronous route generation process using
    the specified vehicles for deliveries scheduled on the given date.

    Args:
        request: Route generation parameters including date and vehicle IDs
        port: Delivery port for service communication
        user: Authenticated user information

    Returns:
        RouteGenerationResponse with confirmation of the operation
    """
    user_id = user.get("sub")
    logger.info(
        f"Request: POST /routes/generate: user_id={user_id}, "
        f"fecha_entrega_estimada={request.fecha_entrega_estimada}, vehicles={len(request.vehicle_ids)}"
    )

    try:
        return await port.generate_routes(request)
    except MicroserviceValidationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data: {e.message}")
    except MicroserviceConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Delivery service unavailable: {e.message}")
    except MicroserviceHTTPError as e:
        raise HTTPException(status_code=e.status_code, detail=f"Delivery service error: {e.message}")


@router.get(
    "/routes",
    response_model=RoutesListResponse,
    responses={
        200: {"description": "List of routes"},
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Requires web_users group"},
        422: {"description": "Invalid query parameters", "model": ValidationErrorResponse},
        503: {"description": "Delivery service unavailable", "model": ServiceUnavailableErrorResponse},
    },
)
async def get_routes(
    fecha_ruta: Optional[date] = Query(None, description="Filter by route date"),
    estado_ruta: Optional[str] = Query(None, description="Filter by route status"),
    port: DeliveryPort = Depends(get_web_delivery_port),
    user: Dict = Depends(require_web_user),
):
    """
    Retrieve routes with optional filters.

    Args:
        fecha_ruta: Optional date filter for routes
        estado_ruta: Optional status filter for routes
        port: Delivery port for service communication
        user: Authenticated user information

    Returns:
        RoutesListResponse with list of routes matching the filters
    """
    user_id = user.get("sub")
    logger.info(
        f"Request: GET /routes: user_id={user_id}, "
        f"fecha_ruta={fecha_ruta}, estado_ruta={estado_ruta}"
    )

    try:
        return await port.list_routes(fecha_ruta=fecha_ruta, estado_ruta=estado_ruta)
    except MicroserviceValidationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data: {e.message}")
    except MicroserviceConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Delivery service unavailable: {e.message}")
    except MicroserviceHTTPError as e:
        raise HTTPException(status_code=e.status_code, detail=f"Delivery service error: {e.message}")


@router.get(
    "/routes/{route_id}",
    response_model=RouteDetailResponse,
    responses={
        200: {"description": "Route details with shipments"},
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Requires web_users group"},
        404: {"description": "Route not found", "model": NotFoundErrorResponse},
        503: {"description": "Delivery service unavailable", "model": ServiceUnavailableErrorResponse},
    },
)
async def get_route(
    route_id: UUID,
    port: DeliveryPort = Depends(get_web_delivery_port),
    user: Dict = Depends(require_web_user),
):
    """
    Get detailed information for a specific route.

    Args:
        route_id: The UUID of the route to retrieve
        port: Delivery port for service communication
        user: Authenticated user information

    Returns:
        RouteDetailResponse with route details and associated shipments
    """
    user_id = user.get("sub")
    logger.info(f"Request: GET /routes/{route_id}: user_id={user_id}")

    try:
        return await port.get_route(route_id)
    except MicroserviceValidationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data: {e.message}")
    except MicroserviceConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Delivery service unavailable: {e.message}")
    except MicroserviceHTTPError as e:
        raise HTTPException(status_code=e.status_code, detail=f"Delivery service error: {e.message}")


@router.patch(
    "/routes/{route_id}/status",
    response_model=RouteResponse,
    responses={
        200: {"description": "Route status updated successfully"},
        400: {"description": "Invalid status value", "model": ValidationErrorResponse},
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Requires web_users group"},
        404: {"description": "Route not found", "model": NotFoundErrorResponse},
        503: {"description": "Delivery service unavailable", "model": ServiceUnavailableErrorResponse},
    },
)
async def update_route_status(
    route_id: UUID,
    request: RouteStatusUpdateRequest,
    port: DeliveryPort = Depends(get_web_delivery_port),
    user: Dict = Depends(require_web_user),
):
    """
    Update the status of a route.

    Args:
        route_id: The UUID of the route to update
        request: New status data
        port: Delivery port for service communication
        user: Authenticated user information

    Returns:
        RouteResponse with updated route information
    """
    user_id = user.get("sub")
    logger.info(
        f"Request: PATCH /routes/{route_id}/status: user_id={user_id}, "
        f"estado_ruta={request.estado_ruta}"
    )

    try:
        return await port.update_route_status(route_id, request.estado_ruta)
    except MicroserviceValidationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data: {e.message}")
    except MicroserviceConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Delivery service unavailable: {e.message}")
    except MicroserviceHTTPError as e:
        raise HTTPException(status_code=e.status_code, detail=f"Delivery service error: {e.message}")


# Vehicles Management Endpoints

@router.get(
    "/vehicles",
    response_model=VehiclesListResponse,
    responses={
        200: {"description": "List of all vehicles"},
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Requires web_users group"},
        503: {"description": "Delivery service unavailable", "model": ServiceUnavailableErrorResponse},
    },
)
async def get_vehicles(
    port: DeliveryPort = Depends(get_web_delivery_port),
    user: Dict = Depends(require_web_user),
):
    """
    Retrieve all vehicles.

    Args:
        port: Delivery port for service communication
        user: Authenticated user information

    Returns:
        VehiclesListResponse with list of all vehicles
    """
    user_id = user.get("sub")
    logger.info(f"Request: GET /vehicles: user_id={user_id}")

    try:
        return await port.list_vehicles()
    except MicroserviceValidationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data: {e.message}")
    except MicroserviceConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Delivery service unavailable: {e.message}")
    except MicroserviceHTTPError as e:
        raise HTTPException(status_code=e.status_code, detail=f"Delivery service error: {e.message}")


@router.post(
    "/vehicles",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Vehicle created successfully"},
        400: {"description": "Invalid vehicle data", "model": ValidationErrorResponse},
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Requires web_users group"},
        422: {"description": "Validation error", "model": ValidationErrorResponse},
        503: {"description": "Delivery service unavailable", "model": ServiceUnavailableErrorResponse},
    },
)
async def create_vehicle(
    request: VehicleCreateRequest,
    port: DeliveryPort = Depends(get_web_delivery_port),
    user: Dict = Depends(require_web_user),
):
    """
    Create a new vehicle.

    Args:
        request: Vehicle creation data
        port: Delivery port for service communication
        user: Authenticated user information

    Returns:
        VehicleResponse with created vehicle information
    """
    user_id = user.get("sub")
    logger.info(
        f"Request: POST /vehicles: user_id={user_id}, "
        f"placa={request.placa}, driver_name={request.driver_name}"
    )

    try:
        return await port.create_vehicle(request)
    except MicroserviceValidationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data: {e.message}")
    except MicroserviceConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Delivery service unavailable: {e.message}")
    except MicroserviceHTTPError as e:
        raise HTTPException(status_code=e.status_code, detail=f"Delivery service error: {e.message}")


@router.put(
    "/vehicles/{vehicle_id}",
    response_model=VehicleResponse,
    responses={
        200: {"description": "Vehicle updated successfully"},
        400: {"description": "Invalid vehicle data", "model": ValidationErrorResponse},
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Requires web_users group"},
        404: {"description": "Vehicle not found", "model": NotFoundErrorResponse},
        422: {"description": "Validation error", "model": ValidationErrorResponse},
        503: {"description": "Delivery service unavailable", "model": ServiceUnavailableErrorResponse},
    },
)
async def update_vehicle(
    vehicle_id: UUID,
    request: VehicleUpdateRequest,
    port: DeliveryPort = Depends(get_web_delivery_port),
    user: Dict = Depends(require_web_user),
):
    """
    Update an existing vehicle.

    Args:
        vehicle_id: The UUID of the vehicle to update
        request: Vehicle update data
        port: Delivery port for service communication
        user: Authenticated user information

    Returns:
        VehicleResponse with updated vehicle information
    """
    user_id = user.get("sub")
    logger.info(f"Request: PUT /vehicles/{vehicle_id}: user_id={user_id}")

    try:
        return await port.update_vehicle(vehicle_id, request)
    except MicroserviceValidationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data: {e.message}")
    except MicroserviceConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Delivery service unavailable: {e.message}")
    except MicroserviceHTTPError as e:
        raise HTTPException(status_code=e.status_code, detail=f"Delivery service error: {e.message}")


@router.delete(
    "/vehicles/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Vehicle deleted successfully"},
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Requires web_users group"},
        404: {"description": "Vehicle not found", "model": NotFoundErrorResponse},
        503: {"description": "Delivery service unavailable", "model": ServiceUnavailableErrorResponse},
    },
)
async def delete_vehicle(
    vehicle_id: UUID,
    port: DeliveryPort = Depends(get_web_delivery_port),
    user: Dict = Depends(require_web_user),
):
    """
    Delete a vehicle.

    Args:
        vehicle_id: The UUID of the vehicle to delete
        port: Delivery port for service communication
        user: Authenticated user information

    Returns:
        204 No Content on success
    """
    user_id = user.get("sub")
    logger.info(f"Request: DELETE /vehicles/{vehicle_id}: user_id={user_id}")

    try:
        await port.delete_vehicle(vehicle_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except MicroserviceValidationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data: {e.message}")
    except MicroserviceConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Delivery service unavailable: {e.message}")
    except MicroserviceHTTPError as e:
        raise HTTPException(status_code=e.status_code, detail=f"Delivery service error: {e.message}")


# Shipments Management Endpoints

@router.patch(
    "/shipments/{order_id}/status",
    response_model=ShipmentResponse,
    responses={
        200: {"description": "Shipment status updated successfully"},
        400: {"description": "Invalid status value", "model": ValidationErrorResponse},
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Requires web_users group"},
        404: {"description": "Shipment not found", "model": NotFoundErrorResponse},
        503: {"description": "Delivery service unavailable", "model": ServiceUnavailableErrorResponse},
    },
)
async def update_shipment_status(
    order_id: UUID,
    request: ShipmentStatusUpdateRequest,
    port: DeliveryPort = Depends(get_web_delivery_port),
    user: Dict = Depends(require_web_user),
):
    """
    Update the status of a shipment by order ID.

    Args:
        order_id: The UUID of the order whose shipment status to update
        request: New status data
        port: Delivery port for service communication
        user: Authenticated user information

    Returns:
        ShipmentResponse with updated shipment information
    """
    user_id = user.get("sub")
    logger.info(
        f"Request: PATCH /shipments/{order_id}/status: user_id={user_id}, "
        f"shipment_status={request.shipment_status}"
    )

    try:
        return await port.update_shipment_status(order_id, request.shipment_status)
    except MicroserviceValidationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data: {e.message}")
    except MicroserviceConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Delivery service unavailable: {e.message}")
    except MicroserviceHTTPError as e:
        raise HTTPException(status_code=e.status_code, detail=f"Delivery service error: {e.message}")
