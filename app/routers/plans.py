"""Plans router - CRUD operations for saved plans using local PostgreSQL."""

from typing import List, Optional
from uuid import uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Text, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user
from app.models.plans import PlanCreateRequest, PlanResponse, PlanUpdateRequest
from app.database import Base, get_db
from app.services.gpt_backend_client import gpt_backend_client

router = APIRouter(prefix="/plans", tags=["plans"])

class Plan(Base):
    __tablename__ = "plans"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)
    state = Column(String, nullable=False, default="saved", index=True)  # draft, saved, completed
    vibes = Column(JSON, nullable=True, default=list)
    tags = Column(JSON, nullable=True, default=list)
    execution = Column(JSON, nullable=True, default=dict)
    stops = Column(JSON, nullable=False, default=list)
    summary = Column(JSON, nullable=True, default=dict)
    final_recommendations = Column(JSON, nullable=True, default=list)
    extra_data = Column(JSON, nullable=True, default=dict)
    executed = Column(Integer, nullable=False, default=0)  # SQLite uses Integer for boolean
    execution_date = Column(String, nullable=True)
    rating_post_execution = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Legacy fields for backwards compatibility
    vibe = Column(String, nullable=True)
    total_duration = Column(Integer, nullable=True)
    total_distance = Column(Float, nullable=True)

@router.get("", response_model=List[PlanResponse])
async def list_plans(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    state: Optional[str] = None
):
    """List all plans for the current user, optionally filtered by state."""
    stmt = select(Plan).where(Plan.user_id == current_user["id"])
    if state:
        stmt = stmt.where(Plan.state == state)
    stmt = stmt.order_by(Plan.created_at.desc())

    result = await db.execute(stmt)
    plans = result.scalars().all()
    
    return [
        PlanResponse(
            id=plan.id,
            user_id=plan.user_id,
            name=plan.name,
            description=plan.description,
            category=plan.category,
            state=plan.state,
            vibes=plan.vibes or [],
            tags=plan.tags or [],
            execution=plan.execution or {},
            stops=plan.stops,
            summary=plan.summary or {},
            final_recommendations=plan.final_recommendations or [],
            metadata=plan.extra_data or {},
            created_at=plan.created_at.isoformat(),
            updated_at=plan.updated_at.isoformat(),
            executed=bool(plan.executed),
            execution_date=plan.execution_date,
            rating_post_execution=plan.rating_post_execution,
            feedback=plan.feedback,
            # Legacy fields
            vibe=plan.vibe,
            total_duration=plan.total_duration,
            total_distance=plan.total_distance,
        )
        for plan in plans
    ]


@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    payload: PlanCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new plan."""
    # Convert Pydantic models to dict for JSON storage
    stops_data = [stop.model_dump() if hasattr(stop, 'model_dump') else stop for stop in payload.stops]
    execution_data = payload.execution.model_dump() if payload.execution and hasattr(payload.execution, 'model_dump') else (payload.execution or {})
    summary_data = payload.summary.model_dump() if payload.summary and hasattr(payload.summary, 'model_dump') else (payload.summary or {})
    
    plan = Plan(
        id=str(uuid4()),
        user_id=current_user["id"],
        name=payload.name,
        description=payload.description,
        category=payload.category,
        state=payload.state or "saved",
        vibes=payload.vibes or [],
        tags=payload.tags or [],
        execution=execution_data,
        stops=stops_data,
        summary=summary_data,
        final_recommendations=payload.final_recommendations or [],
        extra_data=payload.metadata or {},
        # Legacy fields
        vibe=payload.vibe,
        total_duration=payload.total_duration,
        total_distance=payload.total_distance,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)

    # Best-effort: index plan in Qdrant via agent (non-blocking for UX)
    try:
        await gpt_backend_client.upsert_plan_vector(
            {
                "user_id": current_user["id"],
                "plan_id": plan.id,
                "plan": {
                    "id": plan.id,
                    "user_id": plan.user_id,
                    "name": plan.name,
                    "description": plan.description,
                    "category": plan.category,
                    "state": plan.state,
                    "vibes": plan.vibes or [],
                    "tags": plan.tags or [],
                    "execution": plan.execution or {},
                    "stops": plan.stops or [],
                    "summary": plan.summary or {},
                    "final_recommendations": plan.final_recommendations or [],
                    "metadata": plan.extra_data or {},
                    "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
                },
            }
        )
    except Exception:
        # Best-effort indexing
        pass
    
    return PlanResponse(
        id=plan.id,
        user_id=plan.user_id,
        name=plan.name,
        description=plan.description,
        category=plan.category,
        state=plan.state,
        vibes=plan.vibes or [],
        tags=plan.tags or [],
        execution=plan.execution or {},
        stops=plan.stops,
        summary=plan.summary or {},
        final_recommendations=plan.final_recommendations or [],
        metadata=plan.extra_data or {},
        created_at=plan.created_at.isoformat(),
        updated_at=plan.updated_at.isoformat(),
        executed=bool(plan.executed),
        execution_date=plan.execution_date,
        rating_post_execution=plan.rating_post_execution,
        feedback=plan.feedback,
        # Legacy fields
        vibe=plan.vibe,
        total_duration=plan.total_duration,
        total_distance=plan.total_distance,
    )


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific plan."""
    stmt = select(Plan).where(Plan.id == plan_id, Plan.user_id == current_user["id"])
    result = await db.execute(stmt)
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    return PlanResponse(
        id=plan.id,
        user_id=plan.user_id,
        name=plan.name,
        description=plan.description,
        category=plan.category,
        state=plan.state,
        vibes=plan.vibes or [],
        tags=plan.tags or [],
        execution=plan.execution or {},
        stops=plan.stops,
        summary=plan.summary or {},
        final_recommendations=plan.final_recommendations or [],
        metadata=plan.extra_data or {},
        created_at=plan.created_at.isoformat(),
        updated_at=plan.updated_at.isoformat(),
        executed=bool(plan.executed),
        execution_date=plan.execution_date,
        rating_post_execution=plan.rating_post_execution,
        feedback=plan.feedback,
        # Legacy fields
        vibe=plan.vibe,
        total_duration=plan.total_duration,
        total_distance=plan.total_distance,
    )


@router.put("/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: str,
    payload: PlanCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Replace a plan completely."""
    stmt = select(Plan).where(Plan.id == plan_id, Plan.user_id == current_user["id"])
    result = await db.execute(stmt)
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Convert Pydantic models to dict for JSON storage
    stops_data = [stop.model_dump() if hasattr(stop, 'model_dump') else stop for stop in payload.stops]
    execution_data = payload.execution.model_dump() if payload.execution and hasattr(payload.execution, 'model_dump') else (payload.execution or {})
    summary_data = payload.summary.model_dump() if payload.summary and hasattr(payload.summary, 'model_dump') else (payload.summary or {})
    
    plan.name = payload.name
    plan.description = payload.description
    plan.category = payload.category
    plan.state = payload.state or plan.state
    plan.vibes = payload.vibes or []
    plan.tags = payload.tags or []
    plan.execution = execution_data
    plan.stops = stops_data
    plan.summary = summary_data
    plan.final_recommendations = payload.final_recommendations or []
    plan.extra_data = payload.metadata or {}
    plan.updated_at = datetime.utcnow()
    
    # Legacy fields
    plan.vibe = payload.vibe
    plan.total_duration = payload.total_duration
    plan.total_distance = payload.total_distance
    
    await db.commit()
    await db.refresh(plan)
    
    return PlanResponse(
        id=plan.id,
        user_id=plan.user_id,
        name=plan.name,
        description=plan.description,
        category=plan.category,
        state=plan.state,
        vibes=plan.vibes or [],
        tags=plan.tags or [],
        execution=plan.execution or {},
        stops=plan.stops,
        summary=plan.summary or {},
        final_recommendations=plan.final_recommendations or [],
        metadata=plan.extra_data or {},
        created_at=plan.created_at.isoformat(),
        updated_at=plan.updated_at.isoformat(),
        executed=bool(plan.executed),
        execution_date=plan.execution_date,
        rating_post_execution=plan.rating_post_execution,
        feedback=plan.feedback,
        # Legacy fields
        vibe=plan.vibe,
        total_duration=plan.total_duration,
        total_distance=plan.total_distance,
    )


@router.patch("/{plan_id}", response_model=PlanResponse)
async def patch_plan(
    plan_id: str,
    payload: PlanUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Partially update a plan (only specified fields)."""
    stmt = select(Plan).where(Plan.id == plan_id, Plan.user_id == current_user["id"])
    result = await db.execute(stmt)
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Phase 6: AI-assisted edit path (PATCH, but computed by agent with full context)
    if payload.ai_edit is not None:
        agent_payload = {
            "user_id": current_user["id"],
            "plan_id": plan.id,
            "plan": {
                "id": plan.id,
                "user_id": plan.user_id,
                "name": plan.name,
                "description": plan.description,
                "category": plan.category,
                "state": plan.state,
                "vibes": plan.vibes or [],
                "tags": plan.tags or [],
                "execution": plan.execution or {},
                "stops": plan.stops or [],
                "summary": plan.summary or {},
                "final_recommendations": plan.final_recommendations or [],
                "metadata": plan.extra_data or {},
            },
            "edit": payload.ai_edit,
        }

        try:
            agent_result = await gpt_backend_client.edit_plan(agent_payload)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Failed to reach agent for plan edit: {exc}") from exc

        if not agent_result.get("success"):
            raise HTTPException(status_code=400, detail=agent_result.get("error") or "Plan edit failed")

        updated_plan = agent_result.get("updated_plan") or {}
        # Persist updated fields (keep same plan.id)
        if updated_plan.get("name"):
            plan.name = updated_plan["name"]
        plan.description = updated_plan.get("description", plan.description)
        plan.category = updated_plan.get("category", plan.category)
        if isinstance(updated_plan.get("vibes"), list):
            plan.vibes = updated_plan["vibes"]
        if isinstance(updated_plan.get("tags"), list):
            plan.tags = updated_plan["tags"]
        if isinstance(updated_plan.get("execution"), dict):
            plan.execution = updated_plan["execution"]
        if isinstance(updated_plan.get("stops"), list):
            plan.stops = updated_plan["stops"]
        if isinstance(updated_plan.get("summary"), dict):
            plan.summary = updated_plan["summary"]
        if isinstance(updated_plan.get("final_recommendations"), list):
            plan.final_recommendations = updated_plan["final_recommendations"]

        # store edit metadata for audit/debug
        extra = plan.extra_data or {}
        edits = extra.get("ai_edits") or []
        if not isinstance(edits, list):
            edits = []
        edits.append(
            {
                "at": datetime.utcnow().isoformat(),
                "edit": payload.ai_edit,
                "agent_summary": agent_result.get("summary"),
            }
        )
        extra["ai_edits"] = edits[-20:]  # cap
        plan.extra_data = extra

        plan.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(plan)

        # Best-effort: re-index updated plan in Qdrant via agent
        try:
            await gpt_backend_client.upsert_plan_vector(
                {
                    "user_id": current_user["id"],
                    "plan_id": plan.id,
                    "plan": {
                        "id": plan.id,
                        "user_id": plan.user_id,
                        "name": plan.name,
                        "description": plan.description,
                        "category": plan.category,
                        "state": plan.state,
                        "vibes": plan.vibes or [],
                        "tags": plan.tags or [],
                        "execution": plan.execution or {},
                        "stops": plan.stops or [],
                        "summary": plan.summary or {},
                        "final_recommendations": plan.final_recommendations or [],
                        "metadata": plan.extra_data or {},
                        "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
                    },
                }
            )
        except Exception:
            pass

        return PlanResponse(
            id=plan.id,
            user_id=plan.user_id,
            name=plan.name,
            description=plan.description,
            category=plan.category,
            state=plan.state,
            vibes=plan.vibes or [],
            tags=plan.tags or [],
            execution=plan.execution or {},
            stops=plan.stops,
            summary=plan.summary or {},
            final_recommendations=plan.final_recommendations or [],
            metadata=plan.extra_data or {},
            created_at=plan.created_at.isoformat(),
            updated_at=plan.updated_at.isoformat(),
            executed=bool(plan.executed),
            execution_date=plan.execution_date,
            rating_post_execution=plan.rating_post_execution,
            feedback=plan.feedback,
            # Legacy fields
            vibe=plan.vibe,
            total_duration=plan.total_duration,
            total_distance=plan.total_distance,
        )
    
    # Only update fields that are provided
    if payload.name is not None:
        plan.name = payload.name
    if payload.description is not None:
        plan.description = payload.description
    if payload.category is not None:
        plan.category = payload.category
    if payload.state is not None:
        plan.state = payload.state
    if payload.vibes is not None:
        plan.vibes = payload.vibes
    if payload.tags is not None:
        plan.tags = payload.tags
    if payload.execution is not None:
        execution_data = payload.execution.model_dump() if hasattr(payload.execution, 'model_dump') else payload.execution
        plan.execution = execution_data
    if payload.stops is not None:
        stops_data = [stop.model_dump() if hasattr(stop, 'model_dump') else stop for stop in payload.stops]
        plan.stops = stops_data
    if payload.summary is not None:
        summary_data = payload.summary.model_dump() if hasattr(payload.summary, 'model_dump') else payload.summary
        plan.summary = summary_data
    if payload.final_recommendations is not None:
        plan.final_recommendations = payload.final_recommendations
    if payload.metadata is not None:
        plan.extra_data = payload.metadata
    
    plan.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(plan)

    # Best-effort: re-index plan in Qdrant after manual patch updates
    try:
        await gpt_backend_client.upsert_plan_vector(
            {
                "user_id": current_user["id"],
                "plan_id": plan.id,
                "plan": {
                    "id": plan.id,
                    "user_id": plan.user_id,
                    "name": plan.name,
                    "description": plan.description,
                    "category": plan.category,
                    "state": plan.state,
                    "vibes": plan.vibes or [],
                    "tags": plan.tags or [],
                    "execution": plan.execution or {},
                    "stops": plan.stops or [],
                    "summary": plan.summary or {},
                    "final_recommendations": plan.final_recommendations or [],
                    "metadata": plan.extra_data or {},
                    "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
                },
            }
        )
    except Exception:
        pass
    
    return PlanResponse(
        id=plan.id,
        user_id=plan.user_id,
        name=plan.name,
        description=plan.description,
        category=plan.category,
        state=plan.state,
        vibes=plan.vibes or [],
        tags=plan.tags or [],
        execution=plan.execution or {},
        stops=plan.stops,
        summary=plan.summary or {},
        final_recommendations=plan.final_recommendations or [],
        metadata=plan.extra_data or {},
        created_at=plan.created_at.isoformat(),
        updated_at=plan.updated_at.isoformat(),
        executed=bool(plan.executed),
        execution_date=plan.execution_date,
        rating_post_execution=plan.rating_post_execution,
        feedback=plan.feedback,
        # Legacy fields
        vibe=plan.vibe,
        total_duration=plan.total_duration,
        total_distance=plan.total_distance,
    )


@router.delete("/{plan_id}")
async def delete_plan(
    plan_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a plan."""
    stmt = select(Plan).where(Plan.id == plan_id, Plan.user_id == current_user["id"])
    result = await db.execute(stmt)
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    await db.delete(plan)
    await db.commit()
    
    return {"message": "Plan deleted successfully"}

