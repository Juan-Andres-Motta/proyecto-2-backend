
import asyncio
import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.adapters.input.controllers.common_controller import router as common_router
from src.adapters.input.controllers.route_controller import router as route_router
from src.adapters.input.controllers.shipment_controller import (
    router as shipment_router,
)
from src.adapters.input.controllers.vehicle_controller import router as vehicle_router
from src.adapters.input.sqs_consumer import SQSConsumer
from src.application.use_cases.consume_order_created import ConsumeOrderCreatedUseCase
from src.infrastructure.api.exception_handlers import register_exception_handlers
from src.infrastructure.config.logger import setup_logging
from src.infrastructure.config.settings import settings
from src.infrastructure.database.config import engine
from src.infrastructure.dependencies import (
    get_shipment_repository,
    get_processed_event_repository,
    get_geocoding_service,
)
from sqlalchemy.ext.asyncio import AsyncSession

# Setup logging
setup_logging()

# Get logger for this module
logger = logging.getLogger(__name__)

# Global consumer task
consumer_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup/shutdown."""
    global consumer_task

    # Startup: Start SQS consumer
    logger.info("Starting SQS consumer for order_created events...")

    # Create database session factory and use case
    from sqlalchemy.ext.asyncio import async_sessionmaker
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Keep session for the entire lifecycle
    session = session_maker()

    # Create use case with dependencies
    use_case = ConsumeOrderCreatedUseCase(
        shipment_repository=get_shipment_repository(session),
        processed_event_repository=get_processed_event_repository(session),
        geocoding_service=get_geocoding_service(),
        session=session,
    )

    consumer = SQSConsumer(
        queue_url=settings.sqs_order_events_queue_url,
        region=settings.aws_region,
        access_key_id=settings.aws_access_key_id,
        secret_access_key=settings.aws_secret_access_key,
        endpoint_url=settings.aws_endpoint_url,
        use_case=use_case,
    )

    consumer_task = asyncio.create_task(consumer.start())
    logger.info(f"✅ SQS consumer started: {settings.sqs_order_events_queue_url}")

    yield

    # Shutdown: Stop consumer
    logger.info("Stopping SQS consumer...")
    await consumer.stop()
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
    logger.info("✅ SQS consumer stopped")

    # Close session
    await session.close()
    logger.info("✅ Database session closed")


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    contact={
        "name": settings.app_contact_name,
        "email": settings.app_contact_email,
    },
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    openapi_url=settings.openapi_url,
    lifespan=lifespan,
)

logger.info(f"Starting {settings.app_name} v{settings.app_version}")

# Register exception handlers
register_exception_handlers(app)

app.include_router(common_router, prefix="/delivery")
app.include_router(route_router, prefix="/delivery")
app.include_router(shipment_router, prefix="/delivery")
app.include_router(vehicle_router, prefix="/delivery")
