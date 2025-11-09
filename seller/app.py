import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.adapters.input.consumers.event_handlers import EventHandlers
from src.adapters.input.consumers.sqs_consumer import SQSConsumer
from src.adapters.input.controllers.common_controller import router as common_router
from src.adapters.input.controllers.sales_plan_controller import (
    router as sales_plan_router,
)
from src.adapters.input.controllers.seller_controller import router as seller_router
from src.adapters.input.controllers.visit_controller import router as visit_router
from src.infrastructure.api.exception_handlers import register_exception_handlers
from src.infrastructure.config.logger import setup_logging
from src.infrastructure.config.settings import settings
from src.infrastructure.database.config import async_session

# Setup logging
setup_logging()

# Get logger for this module
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.

    Manages:
    - SQS consumer startup and graceful shutdown
    - Event handler registration
    """
    # Startup: Initialize and start SQS consumer
    logger.info("Starting application lifespan...")

    # Initialize SQS consumer
    consumer = SQSConsumer(
        queue_url=settings.sqs_order_events_queue_url,
        aws_region=settings.aws_region,
        endpoint_url=settings.aws_endpoint_url,
        max_messages=10,
        wait_time_seconds=20,
    )

    # Initialize event handlers with DB session factory
    handlers = EventHandlers(db_session_factory=async_session)

    # Register event handlers
    consumer.register_handler("order_created", handlers.handle_order_created)

    # Start consumer in background task
    consumer_task = asyncio.create_task(consumer.start())
    logger.info("SQS consumer started in background")

    yield

    # Shutdown: Stop SQS consumer gracefully
    logger.info("Shutting down application...")
    await consumer.stop()
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        logger.info("SQS consumer task cancelled")
    logger.info("Application shutdown complete")


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

# Register global exception handlers (like Spring @ControllerAdvice)
register_exception_handlers(app)

logger.info(f"Starting {settings.app_name} v{settings.app_version}")

app.include_router(common_router, prefix="/seller")
app.include_router(seller_router, prefix="/seller")
app.include_router(sales_plan_router, prefix="/seller")
app.include_router(visit_router, prefix="/seller")
