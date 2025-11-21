from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # Application
    app_name: str = Field(default="Delivery Service")
    app_description: str = Field(
        default="Delivery service for route optimization and shipment tracking"
    )
    app_version: str = Field(default="1.0.0")
    app_contact_name: str = Field(default="MediSupply Team")
    app_contact_email: str = Field(default="team@medisupply.com")

    # API
    docs_url: str = Field(default="/delivery/docs")
    redoc_url: str = Field(default="/delivery/redoc")
    openapi_url: str = Field(default="/delivery/openapi.json")

    # Database
    database_url: str = Field(
        default="postgresql://postgres:password@shared-db:5432/medisupply"
    )
    debug_sql: bool = Field(default=False)

    # AWS Configuration
    aws_region: str = Field(default="us-east-1")
    aws_access_key_id: str = Field(default="test")
    aws_secret_access_key: str = Field(default="test")
    aws_endpoint_url: str | None = Field(default=None)

    # SQS Configuration (Consumer)
    sqs_order_events_queue_url: str = Field(
        default="http://localstack:4566/000000000000/medisupply-order-events-delivery-queue"
    )

    # SQS Configuration (Publisher)
    sqs_routes_generated_queue_url: str = Field(
        default="http://localstack:4566/000000000000/medisupply-delivery-routes-generated-queue"
    )

    # Nominatim Configuration
    nominatim_base_url: str = Field(default="https://nominatim.openstreetmap.org")
    nominatim_rate_limit_seconds: float = Field(default=1.0)

    # Logging
    log_level: str = Field(default="INFO")


settings = Settings()
