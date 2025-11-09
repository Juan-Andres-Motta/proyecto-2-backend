from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # Application metadata
    app_name: str = Field(default="Seller Service")
    app_description: str = Field(
        default="Seller service built with FastAPI following hexagonal architecture"
    )
    app_version: str = Field(default="1.0.0")
    app_contact_name: str = Field(default="Your Name")
    docs_url: str = Field(default="/seller/docs")
    redoc_url: str = Field(default="/seller/redoc")
    openapi_url: str = Field(default="/seller/openapi.json")

    # Logging
    log_level: str = Field(default="INFO")
    app_contact_email: str = Field(default="you@example.com")

    # Database
    database_url: str = Field(
        default="postgresql://postgres:password@seller-db:5432/seller"
    )
    debug_sql: bool = Field(default=False)

    # External Services
    client_url: str = Field(
        default="http://localhost:8000",
        description="Base URL for the Client Service API"
    )

    # AWS Configuration
    s3_evidence_bucket: str = Field(
        default="test-evidence-bucket",
        description="S3 bucket name for storing visit evidence files"
    )

    # Event Consumption Configuration
    # NEW: Dedicated SQS queue for Seller service (subscribed to SNS topic)
    sqs_order_events_queue_url: str = Field(
        default="https://localstack:4566/000000000000/medisupply-order-events-seller-queue",
        description="SQS queue URL for consuming order events (Seller-specific queue)"
    )

    aws_region: str = Field(
        default="us-east-1",
        description="AWS region for S3 and other AWS services"
    )
    aws_endpoint_url: str | None = Field(
        default=None,
        description="AWS endpoint URL (for LocalStack in development, None for real AWS)"
    )


settings = Settings()
