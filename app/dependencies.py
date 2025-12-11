"""Dependencies for FastAPI routes."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from typing import Optional
import jwt
from jwt import PyJWKClient
import logging

logger = logging.getLogger(__name__)

# HTTP Bearer token security
security = HTTPBearer()


def verify_auth0_token(token: str) -> dict:
    """
    Validate an Auth0 JWT token and return user info.
    
    Args:
        token: JWT token from Auth0
        
    Returns:
        dict with user information (id, email, etc.)
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        # Get Auth0 domain and construct JWKS URL
        auth0_domain = settings.auth0_domain
        if not auth0_domain:
            logger.warning("Auth0 domain not configured, skipping token validation")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Auth0 not configured on server",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Construct JWKS URL
        jwks_url = f"https://{auth0_domain}/.well-known/jwks.json"
        
        # Get the signing key
        jwks_client = PyJWKClient(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # Decode and validate the token
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.auth0_audience,
            issuer=f"https://{auth0_domain}/",
        )
        
        # Extract user info from token
        user_id = payload.get("sub")  # Auth0 user ID
        email = payload.get("email") or payload.get(f"https://{auth0_domain}/email")
        name = payload.get("name") or payload.get(f"https://{auth0_domain}/name")
        
        return {
            "id": user_id,
            "email": email,
            "name": name,
            "user_metadata": payload,
        }
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as exc:
        logger.error(f"Token validation error: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(exc)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_user_token(token: str) -> dict:
    """
    Validate Auth0 JWT token and return user info.
    """
    return verify_auth0_token(token)


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

