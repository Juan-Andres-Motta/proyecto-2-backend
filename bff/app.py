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
    consumer_task = None

    if settings.sqs_queue_url:
        logger.info("Starting SQS consumer...")

        # Create consumer with handlers
        consumer = SQSConsumer(
            queue_url=settings.sqs_queue_url,
            aws_region=settings.sqs_region,
            max_messages=settings.sqs_max_messages,
            wait_time_seconds=settings.sqs_wait_time_seconds,
        )

        # Register event handlers
        publisher = get_publisher()
        handlers = EventHandlers(publisher)

        consumer.register_handler("web_report_generated", handlers.handle_web_report_generated)
        consumer.register_handler("web_delivery_routes", handlers.handle_web_delivery_routes)
        consumer.register_handler("mobile_seller_visit_routes", handlers.handle_mobile_seller_visit_routes)
        consumer.register_handler("order_creation", handlers.handle_order_creation)

        # Start consumer in background
        consumer_task = asyncio.create_task(consumer.start())
        app.state.sqs_consumer = consumer
    else:
        logger.info("SQS queue URL not configured - skipping consumer startup")

    yield

    # Shutdown
    if consumer_task and settings.sqs_queue_url:
        logger.info("Stopping SQS consumer...")
        await app.state.sqs_consumer.stop()
        await consumer_task


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
