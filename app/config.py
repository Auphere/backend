"""Configuration settings for the application."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Supabase Configuration
    supabase_url: str
    supabase_publishable_key: Optional[str] = None  # new public key
    supabase_api_key: Optional[str] = None  # new server-side key
    # Legacy keys (kept for backwards compatibility)
    supabase_secret_key: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_role_key: Optional[str] = None
    
    # Google Places API (legacy fallback)
    google_places_api_key: Optional[str] = None
    
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
    frontend_url: str = "http://localhost:3000"
    
    # Environment
    environment: str = "development"

    # GPT Backend integration
    gpt_backend_url: str = "http://localhost:8001"
    gpt_backend_ws_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def client_api_key(self) -> str:
        """Get the client API key."""
        return self.supabase_publishable_key or self.supabase_anon_key
    
    @property
    def admin_api_key(self) -> str:
        """Get the admin API key."""
        return (
            self.supabase_api_key
            or self.supabase_secret_key
            or self.supabase_service_role_key
        )


# Global settings instance
settings = Settings()
