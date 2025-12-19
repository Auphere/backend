"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, places, plans, chat, geocoding

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
app.include_router(geocoding.router, prefix="/api/v1")


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
    
    return {
        "status": "ok",
        "auth0_configured": bool(settings.auth0_domain),
        "auth0_domain": settings.auth0_domain if settings.auth0_domain else "NOT_SET",
        "auth0_audience": settings.auth0_audience if settings.auth0_audience else "NOT_SET",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )

