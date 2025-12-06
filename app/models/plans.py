"""Pydantic models for user plans."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PlanStop(BaseModel):
    """Represents a single stop within an evening plan."""

    activity: str
    duration: int = Field(..., description="Duration in minutes")
    start_time: str = Field(..., description="Start time (e.g., '19:00')")
    place: Dict[str, Any] = Field(..., description="Place metadata snapshot")


class PlanBase(BaseModel):
    """Common fields for plans."""

    name: str = Field(..., description="Plan name")
    description: Optional[str] = Field(None, description="Short description")
    vibe: Optional[str] = Field(None, description="Primary vibe label")
    total_duration: int = Field(..., description="Total duration in minutes")
    total_distance: float = Field(..., description="Total distance in km")
    stops: List[PlanStop] = Field(..., description="Stops that compose the plan")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PlanCreateRequest(PlanBase):
    """Plan creation payload."""

    pass


class PlanResponse(PlanBase):
    """Plan response returned to clients."""

    id: str
    user_id: str
    created_at: Optional[str] = None

