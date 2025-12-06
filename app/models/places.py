"""Pydantic models for Places."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class CategoryEnum(str, Enum):
    """Place categories."""
    RESTAURANT = "restaurant"
    BAR = "bar"
    CLUB = "night_club"
    CAFE = "cafe"
    LOUNGE = "lounge"
    ACTIVITY = "activity"


class VibeEnum(str, Enum):
    """Place vibes."""
    ROMANTIC = "romantic"
    CASUAL = "casual"
    ENERGETIC = "energetic"
    CHILL = "chill"
    SOPHISTICATED = "sophisticated"
    FUN = "fun"


class PlaceSearchRequest(BaseModel):
    """Request model for place search."""
    query: Optional[str] = Field(None, description="Search query")
    city: Optional[str] = Field(None, description="City to search in")
    min_rating: Optional[float] = Field(
        None, ge=0, le=5, description="Minimum Google rating"
    )
    
    # Filters
    categories: Optional[List[CategoryEnum]] = Field(None, description="Filter by categories")
    vibes: Optional[List[VibeEnum]] = Field(None, description="Filter by vibes")
    
    # Location
    latitude: Optional[float] = Field(None, description="Center latitude")
    longitude: Optional[float] = Field(None, description="Center longitude")
    radius: int = Field(5000, ge=100, le=50000, description="Search radius in meters")
    
    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Results per page")


class PlaceResponse(BaseModel):
    """Response model for a place."""
    place_id: str
    name: str
    formatted_address: Optional[str] = None
    vicinity: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    types: List[str] = []
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    price_level: Optional[int] = None
    phone_number: Optional[str] = None
    website: Optional[str] = None
    opening_hours: Optional[Dict[str, Any]] = None
    
    # Custom attributes
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)
    
    # Computed fields for UI
    distance_km: Optional[float] = None
    is_open: Optional[bool] = None


class PlaceSearchResponse(BaseModel):
    """Paginated response for place search."""
    places: List[PlaceResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

