"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, places, plans, chat
from app.routers import chat

# Create FastAPI app
app = FastAPI(
    title="Auphere API",
    description="Backend API for Auphere - Intelligent Place Discovery",
    version="1.0.0",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(places.router, prefix="/api/v1")
app.include_router(plans.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Auphere API",
        "version": "1.0.0",
        "docs": "/docs" if settings.environment == "development" else "disabled",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/debug/config")
async def debug_config():
    """Debug endpoint to check configuration (development only)."""
    if settings.environment != "development":
        return {"error": "Not available in production"}
    
    def mask_key(key: str) -> str:
        """Mask API key showing only first/last 4 chars."""
        if not key:
            return "NOT_SET"
        if len(key) < 12:
            return f"{key[:4]}...{key[-4:]}"
        return f"{key[:8]}...{key[-8:]}"
    
    try:
        client_key = settings.client_api_key
        admin_key = settings.admin_api_key
    except ValueError as e:
        return {
            "error": str(e),
            "supabase_url": settings.supabase_url if settings.supabase_url else "NOT_SET",
            "env_values": {
                "supabase_publishable_key": mask_key(settings.supabase_publishable_key or ""),
                "supabase_secret_key": mask_key(settings.supabase_secret_key or ""),
                "supabase_anon_key": mask_key(settings.supabase_anon_key or ""),
                "supabase_service_role_key": mask_key(settings.supabase_service_role_key or ""),
            }
        }
    
    return {
        "status": "ok",
        "supabase_url": settings.supabase_url,
        "keys_configured": {
            "client_api_key": mask_key(client_key),
            "admin_api_key": mask_key(admin_key),
        },
        "env_values": {
            "supabase_publishable_key": mask_key(settings.supabase_publishable_key or ""),
            "supabase_api_key": mask_key(settings.supabase_api_key or ""),
            "supabase_secret_key": mask_key(settings.supabase_secret_key or ""),
            "supabase_anon_key": mask_key(settings.supabase_anon_key or ""),
            "supabase_service_role_key": mask_key(settings.supabase_service_role_key or ""),
        },
        "key_types": {
            "using_new_keys": bool(settings.supabase_publishable_key and settings.supabase_api_key),
            "using_legacy_keys": bool(settings.supabase_service_role_key or settings.supabase_anon_key),
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )

