"""Pydantic models for user plans."""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class PlanLocation(BaseModel):
    """Location information for a plan stop."""
    
    address: str
    zone: Optional[str] = None
    lat: float
    lng: float
    travel_time_from_previous_minutes: Optional[int] = None
    travel_mode: Optional[Literal["walk", "car", "public"]] = None


class PlanTiming(BaseModel):
    """Timing information for a plan stop."""
    
    recommended_start: str = Field(..., description="Recommended start time (e.g., '20:00')")
    suggested_duration_minutes: int
    estimated_end: str
    expected_occupancy: Optional[str] = None
    occupancy_recommendation: Optional[str] = None


class PlanDetails(BaseModel):
    """Details about a plan stop."""
    
    vibes: List[str] = Field(default_factory=list)
    target_audience: Optional[List[str]] = None
    music: Optional[str] = None
    noise_level: Optional[Literal["low", "medium", "high"]] = None
    average_spend_per_person: Optional[float] = None


class PlanActions(BaseModel):
    """Available actions for a plan stop."""
    
    can_reserve: bool = False
    reservation_url: Optional[str] = None
    google_maps_url: Optional[str] = None
    phone: Optional[str] = None


class PlanAlternative(BaseModel):
    """Alternative venue for a stop."""
    
    name: str
    reason_not_selected: str
    link: Optional[str] = None


class PlanStop(BaseModel):
    """Represents a single stop within a plan."""

    stop_number: int
    local_id: str = Field(..., description="Place ID or reference")
    name: str
    category: str = Field(..., description="e.g., 'restaurant', 'bar', 'club'")
    type_label: Optional[str] = Field(None, description="e.g., 'Italian restaurant', 'Jazz bar'")
    timing: PlanTiming
    location: PlanLocation
    details: PlanDetails
    selection_reasons: List[str] = Field(default_factory=list)
    actions: PlanActions = Field(default_factory=PlanActions)
    alternatives: Optional[List[PlanAlternative]] = None
    personal_tips: Optional[List[str]] = None
    
    # Legacy field for backwards compatibility
    activity: Optional[str] = None
    duration: Optional[int] = None
    start_time: Optional[str] = None
    place: Optional[Dict[str, Any]] = None


class BudgetBreakdown(BaseModel):
    """Budget breakdown for a plan."""
    
    total: float
    per_person: float
    within_budget: bool
    breakdown: Optional[Dict[str, float]] = None


class PlanMetrics(BaseModel):
    """Success metrics for a plan."""
    
    vibe_match_percent: Optional[float] = None
    average_venue_rating: Optional[float] = None
    success_probability_label: Optional[str] = None


class PlanSummary(BaseModel):
    """Summary metrics for a plan."""
    
    total_duration: str = Field(..., description="Human-readable duration (e.g., '3h 45m')")
    total_distance_km: Optional[float] = None
    budget: BudgetBreakdown
    metrics: Optional[PlanMetrics] = None


class PlanExecution(BaseModel):
    """Execution details for a plan."""
    
    date: Optional[str] = None
    start_time: Optional[str] = None
    duration_hours: Optional[float] = None
    city: Optional[str] = None
    zones: Optional[List[str]] = None
    group_size: Optional[int] = None
    group_composition: Optional[str] = None


class PlanBase(BaseModel):
    """Common fields for plans."""

    name: str = Field(..., description="Plan name")
    description: Optional[str] = Field(None, description="Short description")
    category: Optional[str] = Field(None, description="Plan category (romantic_evening, friends_night, etc.)")
    vibes: List[str] = Field(default_factory=list, description="Plan vibes")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    execution: Optional[PlanExecution] = None
    stops: List[PlanStop] = Field(..., description="Stops that compose the plan")
    summary: Optional[PlanSummary] = None
    final_recommendations: Optional[List[str]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Legacy fields for backwards compatibility
    vibe: Optional[str] = Field(None, description="Primary vibe label (deprecated)")
    total_duration: Optional[int] = Field(None, description="Total duration in minutes (deprecated)")
    total_distance: Optional[float] = Field(None, description="Total distance in km (deprecated)")


class PlanCreateRequest(PlanBase):
    """Plan creation payload."""

    state: Optional[Literal["draft", "saved", "completed"]] = "saved"


class PlanUpdateRequest(BaseModel):
    """Plan update payload."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    vibes: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    execution: Optional[PlanExecution] = None
    stops: Optional[List[PlanStop]] = None
    summary: Optional[PlanSummary] = None
    final_recommendations: Optional[List[str]] = None
    state: Optional[Literal["draft", "saved", "completed"]] = None
    metadata: Optional[Dict[str, Any]] = None

    # Phase 6: AI-assisted edits (replan partial) via auphere-agent
    ai_edit: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional AI edit request; when present, backend will call auphere-agent to compute an updated plan before persisting.",
    )


class PlanResponse(PlanBase):
    """Plan response returned to clients."""

    id: str
    user_id: str
    state: str = Field(default="saved", description="Plan state: draft, saved, completed")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    executed: bool = False
    execution_date: Optional[str] = None
    rating_post_execution: Optional[float] = None
    feedback: Optional[str] = None

