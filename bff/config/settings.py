from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

    # Application metadata
    app_name: str = Field(default="BFF Service")
    app_description: str = Field(
        default="Backend For Frontend service aggregating microservices"
    )
    app_version: str = Field(default="1.0.0")
    app_contact_name: str = Field(default="Your Name")
    app_contact_email: str = Field(default="you@example.com")
    docs_url: str = Field(default="/bff/docs")
    redoc_url: str = Field(default="/bff/redoc")
    openapi_url: str = Field(default="/bff/openapi.json")

    # Logging
    log_level: str = Field(default="INFO")

    # Microservices URLs
    catalog_url: str = Field(default="http://catalog:8000/catalog")
    client_url: str = Field(default="http://client:8000/client")
    delivery_url: str = Field(default="http://delivery:8000/delivery")
    inventory_url: str = Field(default="http://inventory:8000/inventory")
    order_url: str = Field(default="http://order:8000/order")
    seller_url: str = Field(default="http://seller:8000/seller")

    # Service communication settings
    service_timeout: float = Field(default=10.0)

    # AWS Cognito Authentication
    aws_cognito_user_pool_id: str = Field(default="")
    aws_cognito_web_client_id: str = Field(default="")
    aws_cognito_mobile_client_id: str = Field(default="")
    aws_cognito_region: str = Field(default="us-east-1")
    jwt_issuer_url: str = Field(default="")
    jwt_jwks_url: str = Field(default="")


settings = Settings()
