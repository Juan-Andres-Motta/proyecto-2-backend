from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # Application metadata
    app_name: str = Field(default="Client Service")
    app_description: str = Field(
        default="Client service built with FastAPI following hexagonal architecture"
    )
    app_version: str = Field(default="1.0.0")
    docs_url: str = Field(default="/client/docs")
    redoc_url: str = Field(default="/client/redoc")
    openapi_url: str = Field(default="/client/openapi.json")

    # Logging
    log_level: str = Field(default="INFO")

    # Database
    database_url: str = Field(
        default="postgresql://postgres:password@client-db:5432/client"
    )
    debug_sql: bool = Field(default=False)


settings = Settings()
