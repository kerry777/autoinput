"""Application configuration using Pydantic Settings"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = Field(default="AutoInput", env="APP_NAME")
    APP_VERSION: str = Field(default="0.1.0", env="APP_VERSION")
    ENV: str = Field(default="development", env="ENV")
    DEBUG: bool = Field(default=True, env="DEBUG")
    SECRET_KEY: str = Field(default="change-me-in-production", env="SECRET_KEY")
    
    # Server
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./data/autoinput.db",
        env="DATABASE_URL"
    )
    
    # Playwright
    HEADLESS: bool = Field(default=False, env="HEADLESS")
    BROWSER: str = Field(default="chromium", env="BROWSER")
    TIMEOUT: int = Field(default=30000, env="TIMEOUT")
    VIEWPORT_WIDTH: int = Field(default=1280, env="VIEWPORT_WIDTH")
    VIEWPORT_HEIGHT: int = Field(default=720, env="VIEWPORT_HEIGHT")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: Optional[str] = Field(default="logs/autoinput.log", env="LOG_FILE")
    
    # Security
    JWT_SECRET_KEY: str = Field(
        default="change-me-in-production",
        env="JWT_SECRET_KEY"
    )
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    
    # File Storage
    UPLOAD_DIR: str = Field(default="data/uploads", env="UPLOAD_DIR")
    EXPORT_DIR: str = Field(default="data/exports", env="EXPORT_DIR")
    TEMPLATE_DIR: str = Field(default="data/templates", env="TEMPLATE_DIR")
    
    # Encryption
    ENCRYPTION_KEY: Optional[str] = Field(default=None, env="ENCRYPTION_KEY")
    
    # Email (Optional)
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: Optional[int] = Field(default=587, env="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(default=None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    NOTIFICATION_EMAIL: Optional[str] = Field(default=None, env="NOTIFICATION_EMAIL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Create settings instance
settings = get_settings()