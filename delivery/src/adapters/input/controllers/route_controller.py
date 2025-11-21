from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.input.schemas.route_schemas import (
    GenerateRoutesRequest,
    GenerateRoutesResponse,
    RouteDetailResponse,
    RouteListResponse,
    RouteResponse,
    RouteStatusUpdateRequest,
    RouteStatusUpdateResponse,
    ShipmentInRoute,
)
from src.application.use_cases.generate_routes import GenerateRoutesUseCase
from src.application.use_cases.get_route import GetRouteUseCase
from src.application.use_cases.list_routes import ListRoutesUseCase
from src.application.use_cases.update_route_status import UpdateRouteStatusUseCase
from src.domain.exceptions import EntityNotFoundError, InvalidStatusTransitionError
from src.infrastructure.database.config import get_db
from src.infrastructure.dependencies import (
    get_generate_routes_use_case,
    get_get_route_use_case,
    get_list_routes_use_case,
    get_shipment_repository,
    get_update_route_status_use_case,
)

router = APIRouter(tags=["Routes"])


@router.post("/routes/generate", response_model=GenerateRoutesResponse, status_code=202)
async def generate_routes(
    request: GenerateRoutesRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
    use_case: GenerateRoutesUseCase = Depends(get_generate_routes_use_case),
):
    """Generate optimized routes for a target date."""
    # Get count of pending shipments (for response)
    shipment_repo = get_shipment_repository(session)
    shipments = await shipment_repo.find_pending_by_date(request.fecha_entrega_estimada)
    num_pending = len(shipments)

    # Run in background
    background_tasks.add_task(
        use_case.execute,
        request.fecha_entrega_estimada,
        request.vehicle_ids,
    )

    return GenerateRoutesResponse(
        message="Route generation started",
        fecha_entrega_estimada=request.fecha_entrega_estimada,
        num_vehicles=len(request.vehicle_ids),
        num_pending_shipments=num_pending,
    )


@router.get("/routes", response_model=RouteListResponse)
async def list_routes(
    fecha_ruta: Optional[date] = Query(None),
    estado_ruta: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    use_case: ListRoutesUseCase = Depends(get_list_routes_use_case),
):
    """List routes with pagination and filters."""
    routes, total = await use_case.execute(
        fecha_ruta=fecha_ruta,
        estado_ruta=estado_ruta,
        page=page,
        page_size=page_size,
    )

    return RouteListResponse(
        items=[RouteResponse(**r) for r in routes],
        total=total,
        page=page,
        size=len(routes),
        has_next=(page * page_size) < total,
        has_previous=page > 1,
    )


@router.get("/routes/{route_id}", response_model=RouteDetailResponse)
async def get_route(
    route_id: UUID,
    use_case: GetRouteUseCase = Depends(get_get_route_use_case),
):
    """Get route details with assigned shipments."""
    try:
        result = await use_case.execute(route_id)
        return RouteDetailResponse(
            id=result["id"],
            vehicle_id=result["vehicle_id"],
            vehicle_plate=result["vehicle_plate"],
            driver_name=result["driver_name"],
            driver_phone=result["driver_phone"],
            fecha_ruta=result["fecha_ruta"],
            estado_ruta=result["estado_ruta"],
            duracion_estimada_minutos=result["duracion_estimada_minutos"],
            total_distance_km=result["total_distance_km"],
            total_orders=result["total_orders"],
            shipments=[ShipmentInRoute(**s) for s in result["shipments"]],
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/routes/{route_id}/status", response_model=RouteStatusUpdateResponse)
async def update_route_status(
    route_id: UUID,
    request: RouteStatusUpdateRequest,
    use_case: UpdateRouteStatusUseCase = Depends(get_update_route_status_use_case),
):
    """Update route status."""
    try:
        route = await use_case.execute(route_id, request.estado_ruta)
        return RouteStatusUpdateResponse(
            id=route.id,
            estado_ruta=route.estado_ruta.value,
            message="Route status updated successfully",
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
