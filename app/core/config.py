from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment variables or .env file.
    Follows 12-factor app principles and keeps secrets out of code.
    """
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    ENVIRONMENT: str = "development"
    
    # PostgreSQL 18 with psycopg 3 connection string
    # Format: postgresql+psycopg://user:password@localhost:5432/pharmacy_management
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/pharmacy_management"
    
    # Security & JWT configuration
    SECRET_KEY: str = "temporary_dev_secret_key_replace_in_env_file"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Singleton settings instance
settings = Settings()
