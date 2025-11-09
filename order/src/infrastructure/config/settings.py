from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # Application metadata
    app_name: str = Field(default="Order Service")
    app_description: str = Field(
        default="Order service built with FastAPI following hexagonal architecture"
    )
    app_version: str = Field(default="1.0.0")
    app_contact_name: str = Field(default="Your Name")
    docs_url: str = Field(default="/order/docs")
    redoc_url: str = Field(default="/order/redoc")
    openapi_url: str = Field(default="/order/openapi.json")

    # Logging
    log_level: str = Field(default="INFO")
    app_contact_email: str = Field(default="you@example.com")

    # Database
    database_url: str = Field(
        default="postgresql://postgres:password@order-db:5432/order"
    )
    debug_sql: bool = Field(default=False)

    # AWS Configuration
    aws_region: str = Field(default="us-east-1")
    s3_reports_bucket: str = Field(default="reports-bucket")
    sqs_reports_queue_url: str = Field(
        default="https://localstack:4566/000000000000/reports-queue"
    )

    # Event Publishing Configuration
    # NEW: SNS topic ARN for publishing order events (fanout pattern)
    sns_order_events_topic_arn: str = Field(
        default="arn:aws:sns:us-east-1:000000000000:medisupply-order-events-topic",
        description="SNS topic ARN for publishing order events (fans out to multiple consumers)"
    )

    # DEPRECATED: Direct SQS publishing (replaced by SNS fanout)
    sqs_order_events_queue_url: str = Field(
        default="https://localstack:4566/000000000000/order-events-queue",
        description="DEPRECATED - Use sns_order_events_topic_arn instead"
    )

    aws_access_key_id: str = Field(default="test")
    aws_secret_access_key: str = Field(default="test")
    aws_endpoint_url: str | None = Field(
        default=None,
        description="AWS endpoint URL (for LocalStack in development, None for real AWS)"
    )


settings = Settings()
