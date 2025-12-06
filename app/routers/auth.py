"""Authentication routes."""
from fastapi import APIRouter, HTTPException, status, Depends
from app.models.auth import (
    LoginRequest,
    RegisterRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    RefreshTokenRequest,
    AuthResponse,
    UserResponse,
)
from app.dependencies import get_supabase_client, get_current_user
from supabase import Client

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=AuthResponse)
async def login(credentials: LoginRequest):
    """
    Login user with email and password.
    
    Args:
        credentials: Login credentials (email and password)
        
    Returns:
        AuthResponse with access token and user data
        
    Raises:
        HTTPException: If login fails
    """
    supabase: Client = get_supabase_client()
    
    try:
        # Sign in with password
        response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password,
        })
        
        if response.session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        # Get user profile from profiles table
        profile = supabase.table("profiles").select("*").eq("id", response.user.id).single().execute()
        
        user_data = {
            "id": response.user.id,
            "email": response.user.email,
            "name": profile.data.get("name") if profile.data else None,
            "avatar_url": profile.data.get("avatar_url") if profile.data else None,
            "created_at": profile.data.get("created_at") if profile.data else None,
        }
        
        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            token_type="bearer",
            expires_in=response.session.expires_in,
            user=user_data,
        )
    except Exception as e:
        error_message = str(e)
        
        # Handle specific Supabase errors
        if "Invalid login credentials" in error_message or "Email not confirmed" in error_message:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {error_message}",
        )


@router.post("/register", response_model=AuthResponse)
async def register(user_data: RegisterRequest):
    """
    Register a new user.
    
    Args:
        user_data: User registration data (name, email, password)
        
    Returns:
        AuthResponse with access token and user data
        
    Raises:
        HTTPException: If registration fails
    """
    supabase: Client = get_supabase_client()
    
    try:
        # Sign up new user
        response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "name": user_data.name,
                }
            }
        })
        
        if response.user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed",
            )
        
        # The profile is created automatically by the database trigger
        # But we need to wait a bit or fetch it
        # Get user profile
        profile = supabase.table("profiles").select("*").eq("id", response.user.id).single().execute()
        
        user_response = {
            "id": response.user.id,
            "email": response.user.email,
            "name": profile.data.get("name") if profile.data else user_data.name,
            "avatar_url": profile.data.get("avatar_url") if profile.data else None,
            "created_at": profile.data.get("created_at") if profile.data else None,
        }
        
        # If email confirmation is enabled, session might be None
        if response.session:
            return AuthResponse(
                access_token=response.session.access_token,
                refresh_token=response.session.refresh_token,
                token_type="bearer",
                expires_in=response.session.expires_in,
                user=user_response,
            )
        else:
            # Return a temporary token or indicate email confirmation is needed
            # For now, we'll create a session manually if needed
            return AuthResponse(
                access_token="",  # Empty if email confirmation required
                token_type="bearer",
                user=user_response,
            )
    except Exception as e:
        error_message = str(e)
        
        # Handle specific Supabase errors
        if "User already registered" in error_message or "already registered" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {error_message}",
        )


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """
    Send password reset email.
    
    Args:
        request: Email address for password reset
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If request fails
    """
    supabase: Client = get_supabase_client()
    
    try:
        # Send password reset email
        # The redirect_to should point to your frontend reset password page
        from app.config import settings
        redirect_url = f"{settings.frontend_url}/reset-password"
        
        response = supabase.auth.reset_password_for_email(
            request.email,
            {
                "redirect_to": redirect_url,
            }
        )
        
        # Always return success to prevent email enumeration
        return {
            "message": "If an account with that email exists, a password reset link has been sent."
        }
    except Exception as e:
        # Still return success to prevent email enumeration
        return {
            "message": "If an account with that email exists, a password reset link has been sent."
        }


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """
    Reset user password with token.
    
    Note: Supabase handles password reset through email links that redirect
    to the frontend. This endpoint can be used to verify tokens or handle
    custom reset flows. The actual password update happens on the frontend
    using the Supabase client.
    
    Args:
        request: Reset password data (token and new password)
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If reset fails
    """
    supabase: Client = get_supabase_client()
    
    try:
        # Exchange the reset token for a session and update password
        # Note: In Supabase, the reset flow typically happens on the frontend
        # This endpoint can verify the token is valid
        response = supabase.auth.verify_otp({
            "token": request.token,
            "type": "recovery"
        })
        
        if response.session:
            # If we have a session, update the password
            supabase.auth.update_user({
                "password": request.password
            })
            return {
                "message": "Password reset successful"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password reset failed: {str(e)}",
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user (from dependency)
        
    Returns:
        UserResponse with user data
        
    Raises:
        HTTPException: If user not found
    """
    supabase: Client = get_supabase_client()
    
    try:
        # Get user profile
        profile = supabase.table("profiles").select("*").eq("id", current_user["id"]).single().execute()
        
        if not profile.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found",
            )
        
        return UserResponse(
            id=current_user["id"],
            email=current_user["email"],
            name=profile.data.get("name"),
            avatar_url=profile.data.get("avatar_url"),
            created_at=profile.data.get("created_at"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user info: {str(e)}",
        )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token.
    
    Args:
        request: Refresh token request with refresh_token
        
    Returns:
        AuthResponse with new access token and user data
        
    Raises:
        HTTPException: If refresh fails
    """
    supabase: Client = get_supabase_client()
    
    try:
        # Refresh session
        response = supabase.auth.refresh_session(request.refresh_token)
        
        if response.session is None or response.user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )
        
        # Get user profile
        profile = supabase.table("profiles").select("*").eq("id", response.user.id).single().execute()
        
        user_data = {
            "id": response.user.id,
            "email": response.user.email,
            "name": profile.data.get("name") if profile.data else None,
            "avatar_url": profile.data.get("avatar_url") if profile.data else None,
            "created_at": profile.data.get("created_at") if profile.data else None,
        }
        
        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            token_type="bearer",
            expires_in=response.session.expires_in,
            user=user_data,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to refresh token: {str(e)}",
        )


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout current user.
    
    Args:
        current_user: Current authenticated user (from dependency)
        
    Returns:
        Success message
    """
    supabase: Client = get_supabase_client()
    
    try:
        # Sign out
        supabase.auth.sign_out()
        
        return {
            "message": "Logged out successfully"
        }
    except Exception as e:
        # Even if sign_out fails, we consider it successful
        # since the token will expire anyway
        return {
            "message": "Logged out successfully"
        }

