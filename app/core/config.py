# import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "AI-Powered News Aggregator"

    # Database settings
    DATABASE_URL: str = "sqlite:///./news_aggregator.db"

    # CORS settings
    BACKEND_CORS_ORIGINS: list[str] = ["*"]

    # Security settings
    SECRET_KEY: str = "YOUR_SECRET_KEY_HERE"  # Change in production!

    # Optional integrations
    SENTRY_DSN: Optional[str] = None

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
