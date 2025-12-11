"""Authentication routes.

Note: Authentication is now handled by Auth0.
Most endpoints are deprecated. Frontend should use Auth0 Universal Login.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from app.models.auth import UserResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login")
async def login():
    """
    Login endpoint - DEPRECATED.
    
    Authentication is now handled by Auth0.
    Please use Auth0 Universal Login instead.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Login is now handled by Auth0. Please use Auth0 Universal Login."
    )


@router.post("/register")
async def register():
    """
    Register endpoint - DEPRECATED.
    
    Authentication is now handled by Auth0.
    Please use Auth0 Universal Login instead.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Registration is now handled by Auth0. Please use Auth0 Universal Login."
    )


@router.post("/forgot-password")
async def forgot_password():
    """
    Forgot password endpoint - DEPRECATED.
    
    Password reset is now handled by Auth0.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset is now handled by Auth0."
    )


@router.post("/reset-password")
async def reset_password():
    """
    Reset password endpoint - DEPRECATED.
    
    Password reset is now handled by Auth0.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset is now handled by Auth0."
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information from Auth0 token.
    
    Args:
        current_user: Current authenticated user (from Auth0 token)
        
    Returns:
        UserResponse with user data from Auth0
    """
    try:
        return UserResponse(
            id=current_user["id"],
            email=current_user.get("email"),
            name=current_user.get("name"),
            avatar_url=current_user.get("picture"),
            created_at=None,  # Auth0 doesn't provide created_at in standard claims
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user info: {str(e)}",
        )


@router.post("/refresh")
async def refresh_token():
    """
    Refresh token endpoint - DEPRECATED.
    
    Token refresh is now handled by Auth0 SDK on the frontend.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Token refresh is now handled by Auth0 SDK."
    )


@router.post("/logout")
async def logout():
    """
    Logout endpoint - DEPRECATED.
    
    Logout is now handled by Auth0 SDK on the frontend.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Logout is now handled by Auth0 SDK."
    )
