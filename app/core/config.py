# import os
import os
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
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "")

    # Server settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    STREAMLIT_PORT: int = 8501

    # Azure OpenAI settings
    AZURE_OPENAI_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_VERSION: str = "2023-12-01-preview"
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4"

    # Optional: OpenAI API (alternative to Azure OpenAI)
    OPENAI_API_KEY: Optional[str] = None

    # Optional integrations
    SENTRY_DSN: Optional[str] = None

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields from environment


settings = Settings()
