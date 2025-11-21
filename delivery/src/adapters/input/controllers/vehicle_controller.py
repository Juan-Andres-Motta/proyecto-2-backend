from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.adapters.input.schemas.vehicle_schemas import (
    VehicleCreateRequest,
    VehicleListResponse,
    VehicleResponse,
    VehicleUpdateRequest,
)
from src.application.use_cases.create_vehicle import CreateVehicleUseCase
from src.application.use_cases.delete_vehicle import DeleteVehicleUseCase
from src.application.use_cases.list_vehicles import ListVehiclesUseCase
from src.application.use_cases.update_vehicle import UpdateVehicleUseCase
from src.domain.exceptions import EntityNotFoundError, ValidationError
from src.infrastructure.dependencies import (
    get_create_vehicle_use_case,
    get_delete_vehicle_use_case,
    get_list_vehicles_use_case,
    get_update_vehicle_use_case,
)

router = APIRouter(tags=["Vehicles"])


@router.get("/vehicles", response_model=VehicleListResponse)
async def list_vehicles(
    use_case: ListVehiclesUseCase = Depends(get_list_vehicles_use_case),
):
    """List active vehicles."""
    vehicles = await use_case.execute()
    return VehicleListResponse(
        items=[
            VehicleResponse(
                id=v.id,
                placa=v.placa,
                driver_name=v.driver_name,
                driver_phone=v.driver_phone,
                is_active=v.is_active,
            )
            for v in vehicles
        ],
        total=len(vehicles),
    )


@router.post("/vehicles", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    request: VehicleCreateRequest,
    use_case: CreateVehicleUseCase = Depends(get_create_vehicle_use_case),
):
    """Create a new vehicle."""
    try:
        vehicle = await use_case.execute(
            placa=request.placa,
            driver_name=request.driver_name,
            driver_phone=request.driver_phone,
        )
        return VehicleResponse(
            id=vehicle.id,
            placa=vehicle.placa,
            driver_name=vehicle.driver_name,
            driver_phone=vehicle.driver_phone,
            is_active=vehicle.is_active,
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: UUID,
    request: VehicleUpdateRequest,
    use_case: UpdateVehicleUseCase = Depends(get_update_vehicle_use_case),
):
    """Update a vehicle."""
    try:
        vehicle = await use_case.execute(
            vehicle_id=vehicle_id,
            driver_name=request.driver_name,
            driver_phone=request.driver_phone,
        )
        return VehicleResponse(
            id=vehicle.id,
            placa=vehicle.placa,
            driver_name=vehicle.driver_name,
            driver_phone=vehicle.driver_phone,
            is_active=vehicle.is_active,
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/vehicles/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: UUID,
    use_case: DeleteVehicleUseCase = Depends(get_delete_vehicle_use_case),
):
    """Soft-delete (deactivate) a vehicle."""
    try:
        await use_case.execute(vehicle_id)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
