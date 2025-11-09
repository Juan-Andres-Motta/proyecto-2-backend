import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.auth.controller import router as auth_router
from common.middleware import setup_exception_handlers
from common.realtime import get_publisher
from common.sqs import SQSConsumer, EventHandlers
from config.settings import settings
from web.router import router as web_router
from client_app.router import router as client_app_router
from sellers_app.router import router as sellers_app_router

# Get logger for this module
logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    consumer_tasks = []

    # Get shared publisher and handlers
    publisher = get_publisher()
    handlers = EventHandlers(publisher)

    # Start reports queue consumer
    if settings.sqs_queue_url:
        logger.info(f"Starting SQS reports consumer for {settings.sqs_queue_url}...")

        reports_consumer = SQSConsumer(
            queue_url=settings.sqs_queue_url,
            aws_region=settings.sqs_region,
            max_messages=settings.sqs_max_messages,
            wait_time_seconds=settings.sqs_wait_time_seconds,
        )

        reports_consumer.register_handler("web_report_generated", handlers.handle_web_report_generated)
        reports_consumer.register_handler("web_delivery_routes", handlers.handle_web_delivery_routes)
        reports_consumer.register_handler("mobile_seller_visit_routes", handlers.handle_mobile_seller_visit_routes)

        task = asyncio.create_task(reports_consumer.start())
        consumer_tasks.append((reports_consumer, task))
        app.state.sqs_reports_consumer = reports_consumer
    else:
        logger.info("SQS reports queue URL not configured - skipping reports consumer startup")

    # Start order events queue consumer
    order_events_queue = getattr(settings, 'sqs_order_events_queue_url', None)
    if order_events_queue:
        logger.info(f"Starting SQS order events consumer for {order_events_queue}...")

        order_consumer = SQSConsumer(
            queue_url=order_events_queue,
            aws_region=settings.sqs_region,
            max_messages=settings.sqs_max_messages,
            wait_time_seconds=settings.sqs_wait_time_seconds,
        )

        order_consumer.register_handler("order_created", handlers.handle_order_creation)

        task = asyncio.create_task(order_consumer.start())
        consumer_tasks.append((order_consumer, task))
        app.state.sqs_order_consumer = order_consumer
    else:
        logger.info("SQS order events queue URL not configured - skipping order events consumer startup")

    yield

    # Shutdown
    logger.info("Stopping SQS consumers...")
    for consumer, task in consumer_tasks:
        await consumer.stop()
        await task
    logger.info("All SQS consumers stopped")


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

# Configure exception handling middleware
# This must be registered first to catch exceptions from all other middleware and routes
setup_exception_handlers(app)

# Configure CORS
# TODO: Move hardcoded origins to environment variables/settings (requires terraform update)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://bffproyecto.juanandresdeveloper.com"
    ],
    allow_origin_regex=r"^https://([a-zA-Z0-9-]+\.)?medisupply\.andres-duque\.com$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"Starting {settings.app_name} v{settings.app_version}")

app.include_router(auth_router)
app.include_router(web_router)
app.include_router(client_app_router)
app.include_router(sellers_app_router)


@app.get("/bff/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for BFF service.

    Returns:
        Simple health status response
    """
    return {"status": "ok", "service": "bff"}
