"""Pydantic models for authentication."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class LoginRequest(BaseModel):
    """Login request model."""
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")


class RegisterRequest(BaseModel):
    """Registration request model."""
    name: str = Field(..., min_length=2, description="Name must be at least 2 characters")
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")


class ForgotPasswordRequest(BaseModel):
    """Forgot password request model."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request model."""
    token: str
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str


class AuthResponse(BaseModel):
    """Authentication response model."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    user: dict


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[str] = None

