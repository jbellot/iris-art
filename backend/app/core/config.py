"""Application configuration using Pydantic settings."""

import secrets
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # Application
    APP_NAME: str = "IrisVue"
    DEBUG: bool = False
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_hex(32))

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/iris_art"

    # Redis & Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # S3 Storage (MinIO for development)
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "iris-art"

    # JWT Authentication
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8081"]

    # RevenueCat
    REVENUECAT_API_KEY: str = ""
    REVENUECAT_WEBHOOK_SECRET: str = ""
    REVENUECAT_PUBLIC_API_KEY_IOS: str = ""
    REVENUECAT_PUBLIC_API_KEY_ANDROID: str = ""

    # Monitoring
    SENTRY_DSN: str = ""
    ENVIRONMENT: str = "development"


settings = Settings()
