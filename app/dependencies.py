"""Dependencies for FastAPI routes."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from app.config import settings
from typing import Optional

# Supabase clients
supabase_client: Optional[Client] = None
supabase_admin_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get or create Supabase client with publishable key.
    
    This client respects Row Level Security (RLS) policies.
    Use for client-side operations and user-authenticated requests.
    """
    global supabase_client
    if supabase_client is None:
        supabase_client = create_client(
            settings.supabase_url,
            settings.client_api_key
        )
    return supabase_client


def get_supabase_admin_client() -> Client:
    """
    Get Supabase admin client with secret key.
    
    This client bypasses Row Level Security (RLS) policies.
    Use ONLY for server-side operations that require full database access.
    Never expose this client to the frontend.
    """
    global supabase_admin_client
    if supabase_admin_client is None:
        supabase_admin_client = create_client(
            settings.supabase_url,
            settings.admin_api_key
        )
    return supabase_admin_client


# HTTP Bearer token security
security = HTTPBearer()


def verify_user_token(token: str) -> dict:
    """Validate a Supabase JWT and return user info."""
    try:
        supabase = get_supabase_client()
        response = supabase.auth.get_user(token)
        if response.user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {
            "id": response.user.id,
            "email": response.user.email,
            "user_metadata": response.user.user_metadata,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(exc)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Verify JWT token and return current user.
    """
    token = credentials.credentials
    return verify_user_token(token)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[dict]:
    """
    Get current user if token is provided, otherwise return None.
    
    Args:
        credentials: Optional HTTP Bearer token credentials
        
    Returns:
        User data dictionary or None
    """
    if credentials is None:
        return None
    
    try:
        return verify_user_token(credentials.credentials)
    except HTTPException:
        return None

