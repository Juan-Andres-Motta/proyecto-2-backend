from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.output.adapters import (
    NominatimGeocodingService,
    SQSEventPublisher,
)
from src.adapters.output.repositories import (
    SQLAlchemyProcessedEventRepository,
    SQLAlchemyRouteRepository,
    SQLAlchemyShipmentRepository,
    SQLAlchemyVehicleRepository,
)
from src.application.use_cases.consume_order_created import ConsumeOrderCreatedUseCase
from src.application.use_cases.create_vehicle import CreateVehicleUseCase
from src.application.use_cases.delete_vehicle import DeleteVehicleUseCase
from src.application.use_cases.generate_routes import GenerateRoutesUseCase
from src.application.use_cases.get_route import GetRouteUseCase
from src.application.use_cases.get_shipment_by_order import GetShipmentByOrderUseCase
from src.application.use_cases.list_routes import ListRoutesUseCase
from src.application.use_cases.list_vehicles import ListVehiclesUseCase
from src.application.use_cases.update_route_status import UpdateRouteStatusUseCase
from src.application.use_cases.update_shipment_status import UpdateShipmentStatusUseCase
from src.application.use_cases.update_vehicle import UpdateVehicleUseCase
from src.domain.services.route_optimizer import GreedyRouteOptimizer
from src.infrastructure.config.settings import settings
from src.infrastructure.database.config import get_db


# Repository factories
def get_vehicle_repository(session: AsyncSession) -> SQLAlchemyVehicleRepository:
    return SQLAlchemyVehicleRepository(session)


def get_route_repository(session: AsyncSession) -> SQLAlchemyRouteRepository:
    return SQLAlchemyRouteRepository(session)


def get_shipment_repository(session: AsyncSession) -> SQLAlchemyShipmentRepository:
    return SQLAlchemyShipmentRepository(session)


def get_processed_event_repository(session: AsyncSession) -> SQLAlchemyProcessedEventRepository:
    return SQLAlchemyProcessedEventRepository(session)


# External adapter factories
def get_geocoding_service() -> NominatimGeocodingService:
    return NominatimGeocodingService(
        base_url=settings.nominatim_base_url,
        rate_limit_seconds=settings.nominatim_rate_limit_seconds,
    )


def get_event_publisher() -> SQSEventPublisher:
    return SQSEventPublisher(
        routes_generated_queue_url=settings.sqs_routes_generated_queue_url,
        region=settings.aws_region,
        access_key_id=settings.aws_access_key_id,
        secret_access_key=settings.aws_secret_access_key,
        endpoint_url=settings.aws_endpoint_url,
    )


def get_route_optimizer() -> GreedyRouteOptimizer:
    return GreedyRouteOptimizer()


# Use case factories with dependency injection
async def get_create_vehicle_use_case(
    session: AsyncSession = Depends(get_db),
) -> CreateVehicleUseCase:
    return CreateVehicleUseCase(
        vehicle_repository=get_vehicle_repository(session),
    )


async def get_list_vehicles_use_case(
    session: AsyncSession = Depends(get_db),
) -> ListVehiclesUseCase:
    return ListVehiclesUseCase(
        vehicle_repository=get_vehicle_repository(session),
    )


async def get_update_vehicle_use_case(
    session: AsyncSession = Depends(get_db),
) -> UpdateVehicleUseCase:
    return UpdateVehicleUseCase(
        vehicle_repository=get_vehicle_repository(session),
    )


async def get_delete_vehicle_use_case(
    session: AsyncSession = Depends(get_db),
) -> DeleteVehicleUseCase:
    return DeleteVehicleUseCase(
        vehicle_repository=get_vehicle_repository(session),
    )


async def get_list_routes_use_case(
    session: AsyncSession = Depends(get_db),
) -> ListRoutesUseCase:
    return ListRoutesUseCase(
        route_repository=get_route_repository(session),
        vehicle_repository=get_vehicle_repository(session),
    )


async def get_get_route_use_case(
    session: AsyncSession = Depends(get_db),
) -> GetRouteUseCase:
    return GetRouteUseCase(
        route_repository=get_route_repository(session),
        vehicle_repository=get_vehicle_repository(session),
    )


async def get_update_route_status_use_case(
    session: AsyncSession = Depends(get_db),
) -> UpdateRouteStatusUseCase:
    return UpdateRouteStatusUseCase(
        route_repository=get_route_repository(session),
        shipment_repository=get_shipment_repository(session),
    )


async def get_get_shipment_by_order_use_case(
    session: AsyncSession = Depends(get_db),
) -> GetShipmentByOrderUseCase:
    return GetShipmentByOrderUseCase(
        shipment_repository=get_shipment_repository(session),
        vehicle_repository=get_vehicle_repository(session),
        route_repository=get_route_repository(session),
    )


async def get_update_shipment_status_use_case(
    session: AsyncSession = Depends(get_db),
) -> UpdateShipmentStatusUseCase:
    return UpdateShipmentStatusUseCase(
        shipment_repository=get_shipment_repository(session),
    )


async def get_generate_routes_use_case(
    session: AsyncSession = Depends(get_db),
) -> GenerateRoutesUseCase:
    return GenerateRoutesUseCase(
        shipment_repository=get_shipment_repository(session),
        vehicle_repository=get_vehicle_repository(session),
        route_repository=get_route_repository(session),
        route_optimizer=get_route_optimizer(),
        event_publisher=get_event_publisher(),
    )


async def get_consume_order_created_use_case(
    session: AsyncSession = Depends(get_db),
) -> ConsumeOrderCreatedUseCase:
    return ConsumeOrderCreatedUseCase(
        shipment_repository=get_shipment_repository(session),
        processed_event_repository=get_processed_event_repository(session),
        geocoding_service=get_geocoding_service(),
    )
