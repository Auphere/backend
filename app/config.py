"""Configuration settings for the application."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Auth0 Configuration (authentication)
    auth0_domain: str
    auth0_audience: str = "https://auphere-api"  # API identifier in Auth0
    
    # Google Places API (legacy fallback)
    google_places_api_key: Optional[str] = None
    
    # Perplexity API
    perplexity_api_key: Optional[str] = None
    
    # Internal Auphere Places microservice
    places_service_url: str = "http://127.0.0.1:8002"
    places_service_admin_token: Optional[str] = None
    places_service_default_city: str = "Zaragoza"
    places_service_timeout: float = 10.0
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # Cache TTL (1 hour in seconds) - reduced for fresher data
    cache_ttl_seconds: int = 3600
    
    # FastAPI Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    
    # CORS Configuration
    frontend_url: str = "http://localhost:3000, https://app.auphere.com"
    
    # Environment
    environment: str = "development"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/auphere"

    # GPT Backend integration
    gpt_backend_url: str = "http://localhost:8001"
    gpt_backend_ws_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
