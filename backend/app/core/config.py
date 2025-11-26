"""Application configuration"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    # Note: For async operations, use postgresql+asyncpg://
    # Your external database URL will be converted automatically
    DATABASE_URL: str = "postgresql+asyncpg://aka725:10obzco4QMK9if1Ny8EU4XlW8n24iNOa@dpg-d4gp4kqli9vc73doso30-a.oregon-postgres.render.com/nurix_user_queue"
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    
    # Worker Configuration
    WORKER_POOL_SIZE: int = 3
    WORKER_LEASE_TTL_SECONDS: int = 300
    WORKER_MAX_RETRIES: int = 3
    WORKER_POLL_INTERVAL_SECONDS: int = 1
    
    # Rate Limiting
    DEFAULT_RATE_LIMIT_PER_MINUTE: int = 10
    DEFAULT_MAX_CONCURRENT_JOBS: int = 5
    
    # Frontend
    FRONTEND_PORT: int = 3000
    
    # Debug
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

